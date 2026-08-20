import calendar
import uuid
from datetime import datetime, time

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.loans.models import Loan, LoanPayment


class Command(BaseCommand):

    help = (
        "Rebuild loan payment records based on "
        "loan start date, tenure, EMI and current date"
    )

    def add_arguments(self, parser):

        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing loan payments before rebuilding",
        )

    def handle(self, *args, **options):

        if options["clear"]:

            deleted_count, _ = (
                LoanPayment.objects.all().delete()
            )

            self.stdout.write(
                self.style.WARNING(
                    f"Deleted loan payments: {deleted_count}"
                )
            )

        if LoanPayment.objects.exists():

            self.stdout.write(
                self.style.ERROR(
                    "Loan payment records already exist. "
                    "Run with --clear to rebuild them."
                )
            )

            return

        loans = (
            Loan.objects
            .all()
            .order_by("created_at")
        )

        today = timezone.localdate()

        total_created = 0
        total_skipped = 0

        self.stdout.write(
            f"Loans found: {loans.count()}"
        )

        payments_to_create = []

        with transaction.atomic():

            for loan in loans.iterator():

                created, skipped, payments = (
                    self.generate_payments_for_loan(
                        loan=loan,
                        today=today,
                    )
                )

                payments_to_create.extend(
                    payments
                )

                total_created += created
                total_skipped += skipped

                # Insert periodically to avoid
                # keeping too much data in memory.
                if len(payments_to_create) >= 5000:

                    LoanPayment.objects.bulk_create(
                        payments_to_create,
                        batch_size=1000,
                    )

                    payments_to_create = []

            if payments_to_create:

                LoanPayment.objects.bulk_create(
                    payments_to_create,
                    batch_size=1000,
                )

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                f"Loan payments created: {total_created}"
            )
        )

        self.stdout.write(
            f"Loan payments skipped: {total_skipped}"
        )

        self.stdout.write(
            f"Total loan payments: "
            f"{LoanPayment.objects.count()}"
        )

        self.validate()

    def generate_payments_for_loan(
        self,
        loan,
        today,
    ):

        created_count = 0
        skipped_count = 0
        payments = []

        loan_start_date = loan.created_at.date()

        total_months = (
            loan.tenure_years * 12
        )

        # Calculate how many complete months
        # have passed since the loan started.
        elapsed_months = (
            (today.year - loan_start_date.year) * 12
            + (
                today.month
                - loan_start_date.month
            )
        )

        # Current month should only count as completed
        # if today's day is on or after the loan start day.
        if today.day < loan_start_date.day:

            elapsed_months -= 1

        elapsed_months = max(
            elapsed_months,
            0,
        )

        # Cannot create more payments
        # than the loan tenure.
        payment_count = min(
            elapsed_months,
            total_months,
        )

        if payment_count <= 0:

            return (
                created_count,
                skipped_count,
                payments,
            )

        # Payment day follows next_due_date if available.
        if loan.next_due_date:

            payment_day = (
                loan.next_due_date.day
            )

        else:

            payment_day = (
                loan_start_date.day
            )

        for payment_number in range(
            1,
            payment_count + 1,
        ):

            payment_date = (
                self.calculate_payment_date(
                    loan_start_date=loan_start_date,
                    payment_number=payment_number,
                    payment_day=payment_day,
                )
            )

            # Safety validation:
            # Never create payment before loan.
            if payment_date.date() < loan_start_date:

                skipped_count += 1
                continue

            # Never create future payment.
            if payment_date.date() > today:

                skipped_count += 1
                continue

            payments.append(
                LoanPayment(
                    id=uuid.uuid4(),
                    loan=loan,
                    amount=loan.monthly_emi,
                    payment_date=payment_date,
                    payment_number=payment_number,

                    # We explicitly set created_at because
                    # auto_now_add otherwise uses current time.
                    created_at=payment_date,
                )
            )

            created_count += 1

        return (
            created_count,
            skipped_count,
            payments,
        )

    @staticmethod
    def calculate_payment_date(
        loan_start_date,
        payment_number,
        payment_day,
    ):

        # First payment happens one month
        # after the loan starts.
        month_offset = payment_number

        total_month = (
            loan_start_date.month
            + month_offset
        )

        year = (
            loan_start_date.year
            + (
                (total_month - 1) // 12
            )
        )

        month = (
            (total_month - 1) % 12
        ) + 1

        last_day = calendar.monthrange(
            year,
            month,
        )[1]

        actual_day = min(
            payment_day,
            last_day,
        )

        payment_datetime = datetime.combine(
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
            payment_datetime,
            timezone.get_current_timezone(),
        )

    def validate(self):

        self.stdout.write("")
        self.stdout.write(
            "=" * 100
        )

        self.stdout.write(
            "LOAN PAYMENT VALIDATION"
        )

        self.stdout.write(
            "=" * 100
        )

        invalid_before_loan = 0
        invalid_future_payment = 0
        invalid_amount = 0
        invalid_payment_number = 0
        invalid_excess_payments = 0

        today = timezone.localdate()

        loans = (
            Loan.objects
            .prefetch_related("payments")
        )

        for loan in loans.iterator(chunk_size=500):

            payments = list(
                loan.payments
                .all()
                .order_by("payment_number")
            )

            total_months = (
                loan.tenure_years * 12
            )

            # --------------------------------------------------
            # Validate maximum payment count.
            # --------------------------------------------------

            if len(payments) > total_months:

                invalid_excess_payments += 1

                self.stdout.write(
                    self.style.ERROR(
                        f"\nEXCESS PAYMENTS"
                        f"\nLoan: {loan.id}"
                        f"\nPayments: {len(payments)}"
                        f"\nMaximum: {total_months}"
                    )
                )

            expected_number = 1

            for payment in payments:

                # ----------------------------------------------
                # Validate payment number sequence.
                # ----------------------------------------------

                if (
                    payment.payment_number
                    != expected_number
                ):

                    invalid_payment_number += 1

                    self.stdout.write(
                        self.style.ERROR(
                            f"\nINVALID PAYMENT NUMBER"
                            f"\nLoan: {loan.id}"
                            f"\nExpected: "
                            f"{expected_number}"
                            f"\nActual: "
                            f"{payment.payment_number}"
                        )
                    )

                expected_number += 1

                # ----------------------------------------------
                # Payment cannot happen before loan start.
                # ----------------------------------------------

                if (
                    payment.payment_date.date()
                    < loan.created_at.date()
                ):

                    invalid_before_loan += 1

                    self.stdout.write(
                        self.style.ERROR(
                            f"\nPAYMENT BEFORE LOAN START"
                            f"\nLoan: {loan.id}"
                            f"\nLoan start: "
                            f"{loan.created_at.date()}"
                            f"\nPayment date: "
                            f"{payment.payment_date.date()}"
                        )
                    )

                # ----------------------------------------------
                # Payment cannot be in future.
                # ----------------------------------------------

                if (
                    payment.payment_date.date()
                    > today
                ):

                    invalid_future_payment += 1

                # ----------------------------------------------
                # Payment amount should equal EMI.
                # ----------------------------------------------

                if (
                    payment.amount
                    != loan.monthly_emi
                ):

                    invalid_amount += 1

                    self.stdout.write(
                        self.style.ERROR(
                            f"\nINVALID PAYMENT AMOUNT"
                            f"\nLoan: {loan.id}"
                            f"\nPayment number: "
                            f"{payment.payment_number}"
                            f"\nStored amount: "
                            f"{payment.amount}"
                            f"\nExpected EMI: "
                            f"{loan.monthly_emi}"
                        )
                    )

        self.stdout.write("")
        self.stdout.write(
            "=" * 100
        )

        self.stdout.write(
            "VALIDATION SUMMARY"
        )

        self.stdout.write(
            "=" * 100
        )

        self.stdout.write(
            f"Total loans: "
            f"{Loan.objects.count()}"
        )

        self.stdout.write(
            f"Total loan payments: "
            f"{LoanPayment.objects.count()}"
        )

        self.stdout.write(
            f"Payments before loan start: "
            f"{invalid_before_loan}"
        )

        self.stdout.write(
            f"Future payments: "
            f"{invalid_future_payment}"
        )

        self.stdout.write(
            f"Wrong payment amounts: "
            f"{invalid_amount}"
        )

        self.stdout.write(
            f"Invalid payment sequences: "
            f"{invalid_payment_number}"
        )

        self.stdout.write(
            f"Loans with excess payments: "
            f"{invalid_excess_payments}"
        )

        total_invalid = (
            invalid_before_loan
            + invalid_future_payment
            + invalid_amount
            + invalid_payment_number
            + invalid_excess_payments
        )

        self.stdout.write(
            f"\nTotal validation errors: "
            f"{total_invalid}"
        )

        if total_invalid == 0:

            self.stdout.write(
                self.style.SUCCESS(
                    "\nLOAN PAYMENT VALIDATION PASSED"
                )
            )

        else:

            self.stdout.write(
                self.style.ERROR(
                    "\nLOAN PAYMENT VALIDATION FAILED"
                )
            )