import calendar
import uuid
from datetime import datetime, time

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.banking.models import BankAccount
from apps.loans.models import Loan
from apps.transactions.models import Transaction


class Command(BaseCommand):

    help = (
        "Create monthly EMI debit transactions based on "
        "loan start date, account opening date, and due date"
    )

    def add_arguments(self, parser):

        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing EMI transactions before creating new ones",
        )

    def handle(self, *args, **options):

        if options["clear"]:

            deleted_count, _ = (
                Transaction.objects
                .filter(category="EMI")
                .delete()
            )

            self.stdout.write(
                self.style.WARNING(
                    f"Deleted EMI transactions: {deleted_count}"
                )
            )

        loans = (
            Loan.objects
            .select_related("customer")
            .order_by("created_at")
        )

        total_created = 0
        total_skipped = 0
        loans_without_account = 0

        now = timezone.now()

        self.stdout.write(
            f"Loans found: {loans.count()}"
        )

        with transaction.atomic():

            for loan in loans.iterator():

                account = self.get_account_for_customer(
                    loan.customer_id
                )

                if not account:

                    loans_without_account += 1

                    self.stdout.write(
                        self.style.WARNING(
                            f"Skipping loan {loan.id}: "
                            f"No active bank account found"
                        )
                    )

                    continue

                created, skipped = (
                    self.create_emi_schedule(
                        loan=loan,
                        account=account,
                        now=now,
                    )
                )

                total_created += created
                total_skipped += skipped

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                f"EMI transactions created: {total_created}"
            )
        )

        self.stdout.write(
            f"EMI transactions skipped: {total_skipped}"
        )

        self.stdout.write(
            f"Loans without account: {loans_without_account}"
        )

        self.stdout.write(
            f"Total EMI transactions: "
            f"{Transaction.objects.filter(category='EMI').count()}"
        )

        self.validate()

    @staticmethod
    def get_account_for_customer(customer_id):

        # Prefer savings account.
        account = (
            BankAccount.objects
            .filter(
                customer_id=customer_id,
                status=BankAccount.AccountStatus.ACTIVE,
                account_type=BankAccount.AccountType.SAVINGS,
            )
            .order_by("created_at")
            .first()
        )

        if account:
            return account

        # Fallback to any active account.
        return (
            BankAccount.objects
            .filter(
                customer_id=customer_id,
                status=BankAccount.AccountStatus.ACTIVE,
            )
            .order_by("created_at")
            .first()
        )

    def create_emi_schedule(
        self,
        loan,
        account,
        now,
    ):

        created_count = 0
        skipped_count = 0

        # EMI cannot exist before both:
        #
        # 1. Loan start date
        # 2. Bank account opening date
        #
        # We compare DATE values because transaction
        # timestamps are generated at 10:00 AM.
        start_date = max(
            loan.created_at.date(),
            account.created_at.date(),
        )

        # EMI deduction day comes from next_due_date.
        if loan.next_due_date:

            due_day = loan.next_due_date.day

        else:

            due_day = loan.created_at.day

        current_year = start_date.year
        current_month = start_date.month

        # If this month's due date already happened
        # before the valid start date, start next month.
        first_possible_date = self.build_emi_datetime(
            year=current_year,
            month=current_month,
            due_day=due_day,
        )

        if first_possible_date.date() < start_date:

            current_year, current_month = (
                self.get_next_month(
                    current_year,
                    current_month,
                )
            )

        while True:

            emi_date = self.build_emi_datetime(
                year=current_year,
                month=current_month,
                due_day=due_day,
            )

            # Never create future EMI transactions.
            if emi_date > now:
                break

            # Extra safety validation.
            if (
                emi_date.date() >= loan.created_at.date()
                and emi_date.date() >= account.created_at.date()
            ):

                exists = (
                    Transaction.objects
                    .filter(
                        account=account,
                        category="EMI",
                        transaction_date__date=emi_date.date(),
                        description__contains=str(loan.id),
                    )
                    .exists()
                )

                if exists:

                    skipped_count += 1

                else:

                    Transaction.objects.create(
                        id=uuid.uuid4(),
                        account=account,
                        transaction_type=(
                            Transaction.TransactionType.DEBIT
                        ),
                        amount=loan.monthly_emi,
                        currency="INR",
                        description=(
                            f"EMI payment for "
                            f"{loan.loan_type} loan "
                            f"{loan.id}"
                        ),
                        merchant="LOAN EMI",
                        transaction_date=emi_date,
                        category="EMI",
                        status=(
                            Transaction.TransactionStatus.COMPLETED
                        ),
                    )

                    created_count += 1

            current_year, current_month = (
                self.get_next_month(
                    current_year,
                    current_month,
                )
            )

        return created_count, skipped_count

    @staticmethod
    def get_next_month(year, month):

        if month == 12:
            return year + 1, 1

        return year, month + 1

    @staticmethod
    def build_emi_datetime(
        year,
        month,
        due_day,
    ):

        last_day = calendar.monthrange(
            year,
            month,
        )[1]

        actual_day = min(
            due_day,
            last_day,
        )

        emi_datetime = datetime.combine(
            datetime(
                year,
                month,
                actual_day,
            ).date(),
            time(
                10,
                0,
                0,
            ),
        )

        return timezone.make_aware(
            emi_datetime,
            timezone.get_current_timezone(),
        )

    def validate(self):

        self.stdout.write("")
        self.stdout.write(
            "========== EMI VALIDATION =========="
        )

        invalid_before_account = 0
        invalid_before_loan = 0
        wrong_amount = 0

        emi_transactions = (
            Transaction.objects
            .filter(category="EMI")
            .select_related("account")
        )

        for txn in emi_transactions.iterator():

            loan_id = self.extract_loan_id(
                txn.description
            )

            if not loan_id:
                continue

            try:

                loan = Loan.objects.get(
                    id=loan_id
                )

            except (
                Loan.DoesNotExist,
                ValueError,
            ):

                continue

            # Compare DATE, not exact timestamps.
            #
            # Example:
            # Account created:
            # 2024-05-10 14:00
            #
            # EMI transaction:
            # 2024-05-10 10:00
            #
            # Same calendar day is valid.
            if (
                txn.transaction_date.date()
                < txn.account.created_at.date()
            ):
                invalid_before_account += 1

            if (
                txn.transaction_date.date()
                < loan.created_at.date()
            ):
                invalid_before_loan += 1

            if txn.amount != loan.monthly_emi:

                wrong_amount += 1

        self.stdout.write(
            f"EMI before account opening: "
            f"{invalid_before_account}"
        )

        self.stdout.write(
            f"EMI before loan start: "
            f"{invalid_before_loan}"
        )

        self.stdout.write(
            f"EMI with wrong amount: "
            f"{wrong_amount}"
        )

        if (
            invalid_before_account == 0
            and invalid_before_loan == 0
            and wrong_amount == 0
        ):

            self.stdout.write(
                self.style.SUCCESS(
                    "EMI VALIDATION PASSED"
                )
            )

        else:

            self.stdout.write(
                self.style.ERROR(
                    "EMI VALIDATION FAILED"
                )
            )

    @staticmethod
    def extract_loan_id(description):

        if not description:
            return None

        parts = description.split()

        if not parts:
            return None

        return parts[-1]