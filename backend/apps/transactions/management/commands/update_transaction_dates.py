import calendar
import random
from datetime import datetime, timedelta, time

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from apps.banking.models import BankAccount
from apps.loans.models import Loan
from apps.transactions.models import Transaction


class Command(BaseCommand):

    help = (
        "Update transaction dates based on bank account opening "
        "dates and enforce monthly EMI transaction dates"
    )

    def handle(self, *args, **options):

        random.seed(20260820)

        as_of_datetime = timezone.now()

        total_updated = 0
        total_emi_updated = 0
        total_non_emi_updated = 0

        accounts = list(
            BankAccount.objects.select_related(
                "customer"
            )
        )

        self.stdout.write(
            f"Accounts found: {len(accounts)}"
        )

        with transaction.atomic():

            for account_index, account in enumerate(
                accounts,
                start=1,
            ):

                account_open_date = account.created_at

                customer_loans = list(
                    Loan.objects.filter(
                        customer=account.customer
                    ).order_by("created_at")
                )

                # ------------------------------------------
                # 1. HANDLE EMI TRANSACTIONS
                # ------------------------------------------

                emi_transactions = list(
                    Transaction.objects.filter(
                        account=account,
                        category="EMI",
                    ).order_by("id")
                )

                if customer_loans and emi_transactions:

                    self.update_emi_dates(
                        account=account,
                        loans=customer_loans,
                        transactions=emi_transactions,
                        as_of_datetime=as_of_datetime,
                    )

                    Transaction.objects.bulk_update(
                        emi_transactions,
                        ["transaction_date"],
                        batch_size=1000,
                    )

                    total_emi_updated += len(
                        emi_transactions
                    )

                # ------------------------------------------
                # 2. HANDLE NON-EMI TRANSACTIONS
                # ------------------------------------------

                non_emi_transactions = list(
                    Transaction.objects.filter(
                        account=account
                    ).exclude(
                        category="EMI"
                    )
                )

                if non_emi_transactions:

                    self.update_non_emi_dates(
                        account=account,
                        transactions=non_emi_transactions,
                        as_of_datetime=as_of_datetime,
                    )

                    Transaction.objects.bulk_update(
                        non_emi_transactions,
                        ["transaction_date"],
                        batch_size=5000,
                    )

                    total_non_emi_updated += len(
                        non_emi_transactions
                    )

                total_updated += (
                    len(emi_transactions)
                    + len(non_emi_transactions)
                )

                if account_index % 100 == 0:

                    self.stdout.write(
                        f"Processed "
                        f"{account_index}/{len(accounts)} "
                        f"accounts"
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"Total transactions updated: "
                f"{total_updated}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"EMI transactions updated: "
                f"{total_emi_updated}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Non-EMI transactions updated: "
                f"{total_non_emi_updated}"
            )
        )

        self.validate()

    # ==================================================
    # EMI DATE LOGIC
    # ==================================================

    def update_emi_dates(
        self,
        account,
        loans,
        transactions,
        as_of_datetime,
    ):

        """
        EMI transactions are assigned month-by-month.

        EMI cannot happen before:
        - account opening date
        - loan start date

        The effective EMI start date is therefore the
        later of those two dates.
        """

        emi_schedule = []

        for loan in loans:

            start_date = max(
                loan.created_at,
                account.created_at,
            )

            emi_date = self.get_first_emi_date(
                start_date
            )

            loan_end_date = self.add_years(
                loan.created_at,
                loan.tenure_years,
            )

            end_date = min(
                loan_end_date,
                as_of_datetime,
            )

            while emi_date <= end_date:

                emi_schedule.append(
                    (
                        emi_date,
                        loan,
                    )
                )

                emi_date = self.add_month(
                    emi_date
                )

        emi_schedule.sort(
            key=lambda item: item[0]
        )

        # We may have more or fewer EMI transaction
        # records than the generated monthly schedule.
        #
        # Assign existing transactions to valid months.
        usable_count = min(
            len(transactions),
            len(emi_schedule),
        )

        for index in range(usable_count):

            emi_date, loan = (
                emi_schedule[index]
            )

            transactions[index].transaction_date = (
                self.randomize_emi_time(
                    emi_date
                )
            )

        # If extra EMI transactions exist, keep them
        # within the valid account/loan timeline.
        if len(transactions) > usable_count:

            valid_start = max(
                account.created_at,
                loans[0].created_at,
            )

            for txn in transactions[usable_count:]:

                txn.transaction_date = (
                    self.random_datetime(
                        valid_start,
                        as_of_datetime,
                    )
                )

    # ==================================================
    # NON-EMI DATE LOGIC
    # ==================================================

    def update_non_emi_dates(
        self,
        account,
        transactions,
        as_of_datetime,
    ):

        """
        Every non-EMI transaction is placed somewhere
        between account opening date and now.
        """

        start_datetime = account.created_at

        if start_datetime >= as_of_datetime:
            return

        for txn in transactions:

            txn.transaction_date = (
                self.random_datetime(
                    start_datetime,
                    as_of_datetime,
                )
            )

    # ==================================================
    # DATE HELPERS
    # ==================================================

    @staticmethod
    def get_first_emi_date(start_datetime):

        """
        First EMI occurs approximately one month after
        the loan/account becomes valid.
        """

        return Command.add_month(
            start_datetime
        )

    @staticmethod
    def add_month(value):

        year = value.year
        month = value.month + 1

        if month > 12:
            month = 1
            year += 1

        max_day = calendar.monthrange(
            year,
            month,
        )[1]

        day = min(
            value.day,
            max_day,
        )

        return value.replace(
            year=year,
            month=month,
            day=day,
        )

    @staticmethod
    def add_years(value, years):

        try:
            return value.replace(
                year=value.year + years
            )

        except ValueError:

            return value.replace(
                year=value.year + years,
                month=2,
                day=28,
            )

    @staticmethod
    def randomize_emi_time(emi_datetime):

        hour = random.randint(6, 22)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)

        return emi_datetime.replace(
            hour=hour,
            minute=minute,
            second=second,
            microsecond=0,
        )

    @staticmethod
    def random_datetime(
        start_datetime,
        end_datetime,
    ):

        available_seconds = int(
            (
                end_datetime
                - start_datetime
            ).total_seconds()
        )

        if available_seconds <= 0:
            return start_datetime

        random_seconds = random.randint(
            1,
            available_seconds,
        )

        return (
            start_datetime
            + timedelta(
                seconds=random_seconds
            )
        )

    # ==================================================
    # VALIDATION
    # ==================================================

    def validate(self):

        self.stdout.write("")
        self.stdout.write(
            "========== VALIDATION =========="
        )

        invalid_before_account = 0
        invalid_future = 0

        transactions = (
            Transaction.objects
            .select_related("account")
            .all()
        )

        for txn in transactions.iterator():

            if (
                txn.transaction_date
                < txn.account.created_at
            ):
                invalid_before_account += 1

            if (
                txn.transaction_date
                > timezone.now()
            ):
                invalid_future += 1

        self.stdout.write(
            f"Transactions before account opening: "
            f"{invalid_before_account}"
        )

        self.stdout.write(
            f"Future transactions: "
            f"{invalid_future}"
        )

        if (
            invalid_before_account == 0
            and invalid_future == 0
        ):

            self.stdout.write(
                self.style.SUCCESS(
                    "BASIC VALIDATION PASSED"
                )
            )

        else:

            self.stdout.write(
                self.style.ERROR(
                    "VALIDATION FAILED"
                )
            )