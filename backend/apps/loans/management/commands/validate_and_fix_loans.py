from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.loans.models import Loan


class Command(BaseCommand):

    help = (
        "Validate loan EMI and outstanding amount calculations "
        "and automatically fix invalid outstanding amounts"
    )

    def add_arguments(self, parser):

        parser.add_argument(
            "--fix",
            action="store_true",
            help="Automatically fix invalid outstanding amounts",
        )

    def handle(self, *args, **options):

        fix_records = options["fix"]

        self.stdout.write("")
        self.stdout.write("=" * 100)
        self.stdout.write("LOAN VALIDATION")
        self.stdout.write("=" * 100)

        today = timezone.localdate()

        total_loans = 0
        valid_loans = 0
        invalid_emi = 0
        invalid_outstanding = 0
        invalid_principal = 0
        invalid_dates = 0
        fixed_records = 0

        updates = []

        loans = Loan.objects.all().iterator()

        with transaction.atomic():

            for loan in loans:

                total_loans += 1

                loan_is_valid = True

                # --------------------------------------------------
                # 1. VALIDATE PRINCIPAL
                # --------------------------------------------------

                if loan.principal_amount <= Decimal("0.00"):

                    invalid_principal += 1
                    loan_is_valid = False

                    self.stdout.write(
                        self.style.ERROR(
                            f"\nINVALID PRINCIPAL"
                            f"\nLoan ID: {loan.id}"
                            f"\nPrincipal: {loan.principal_amount}"
                        )
                    )

                    continue

                # --------------------------------------------------
                # 2. VALIDATE LOAN START DATE
                # --------------------------------------------------

                loan_start_date = loan.created_at.date()

                if loan_start_date > today:

                    invalid_dates += 1
                    loan_is_valid = False

                    self.stdout.write(
                        self.style.ERROR(
                            f"\nINVALID LOAN DATE"
                            f"\nLoan ID: {loan.id}"
                            f"\nLoan start: {loan_start_date}"
                            f"\nToday: {today}"
                        )
                    )

                    continue

                # --------------------------------------------------
                # 3. CALCULATE EXPECTED EMI
                #
                # Simple Interest:
                #
                # SI = P × R × T / 100
                #
                # Total Payable = P + SI
                #
                # EMI = Total Payable / Total Months
                # --------------------------------------------------

                expected_emi = (
                    loan.principal_amount
                    * (
                        Decimal("1.00")
                        + (
                            loan.interest_rate
                            * Decimal(loan.tenure_years)
                            / Decimal("100")
                        )
                    )
                    / Decimal(loan.tenure_years * 12)
                ).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP,
                )

                if loan.monthly_emi != expected_emi:

                    invalid_emi += 1
                    loan_is_valid = False

                    self.stdout.write(
                        self.style.ERROR(
                            f"\nINVALID EMI"
                            f"\nLoan ID: {loan.id}"
                            f"\nStored EMI: {loan.monthly_emi}"
                            f"\nExpected EMI: {expected_emi}"
                        )
                    )

                # --------------------------------------------------
                # 4. CALCULATE ELAPSED MONTHS
                # --------------------------------------------------

                elapsed_months = (
                    (today.year - loan_start_date.year) * 12
                    + (
                        today.month
                        - loan_start_date.month
                    )
                )

                # Current month's EMI is counted only if
                # the loan start day has already passed.
                if today.day < loan_start_date.day:

                    elapsed_months -= 1

                elapsed_months = max(
                    elapsed_months,
                    0,
                )

                total_months = (
                    loan.tenure_years * 12
                )

                # A loan cannot have more elapsed months
                # than its total tenure.
                elapsed_months = min(
                    elapsed_months,
                    total_months,
                )

                remaining_months = (
                    total_months
                    - elapsed_months
                )

                # --------------------------------------------------
                # 5. CALCULATE EXPECTED OUTSTANDING AMOUNT
                # --------------------------------------------------

                expected_outstanding = (
                    loan.monthly_emi
                    * Decimal(remaining_months)
                ).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP,
                )

                # --------------------------------------------------
                # 6. VALIDATE STATUS-SPECIFIC RULES
                # --------------------------------------------------

                if loan.status == Loan.LoanStatus.ABOUT_TO_CLOSE:

                    # About-to-close should have a maximum
                    # of 6 remaining EMI payments.
                    if remaining_months > 6:

                        loan_is_valid = False

                        self.stdout.write(
                            self.style.WARNING(
                                f"\nSTATUS / DATE MISMATCH"
                                f"\nLoan ID: {loan.id}"
                                f"\nStatus: {loan.status}"
                                f"\nRemaining months: "
                                f"{remaining_months}"
                            )
                        )

                # --------------------------------------------------
                # 7. VALIDATE OUTSTANDING AMOUNT
                # --------------------------------------------------

                if (
                    loan.outstanding_amount
                    != expected_outstanding
                ):

                    invalid_outstanding += 1
                    loan_is_valid = False

                    self.stdout.write(
                        self.style.WARNING(
                            f"\nINVALID OUTSTANDING AMOUNT"
                            f"\nLoan ID: {loan.id}"
                            f"\nLoan Type: {loan.loan_type}"
                            f"\nPrincipal: "
                            f"{loan.principal_amount}"
                            f"\nInterest Rate: "
                            f"{loan.interest_rate}%"
                            f"\nTenure: "
                            f"{loan.tenure_years} years"
                            f"\nMonthly EMI: "
                            f"{loan.monthly_emi}"
                            f"\nLoan Start: "
                            f"{loan_start_date}"
                            f"\nElapsed Months: "
                            f"{elapsed_months}"
                            f"\nRemaining Months: "
                            f"{remaining_months}"
                            f"\nStored Outstanding: "
                            f"{loan.outstanding_amount}"
                            f"\nExpected Outstanding: "
                            f"{expected_outstanding}"
                        )
                    )

                    if fix_records:

                        loan.outstanding_amount = (
                            expected_outstanding
                        )

                        updates.append(loan)

                        fixed_records += 1

                if loan_is_valid:

                    valid_loans += 1

            # --------------------------------------------------
            # BULK UPDATE
            # --------------------------------------------------

            if fix_records and updates:

                Loan.objects.bulk_update(
                    updates,
                    ["outstanding_amount"],
                    batch_size=500,
                )

        # --------------------------------------------------
        # SUMMARY
        # --------------------------------------------------

        self.stdout.write("")
        self.stdout.write("=" * 100)
        self.stdout.write("VALIDATION SUMMARY")
        self.stdout.write("=" * 100)

        self.stdout.write(
            f"Total loans: {total_loans}"
        )

        self.stdout.write(
            f"Valid loans: {valid_loans}"
        )

        self.stdout.write(
            f"Invalid EMI calculations: {invalid_emi}"
        )

        self.stdout.write(
            f"Invalid outstanding amounts: "
            f"{invalid_outstanding}"
        )

        self.stdout.write(
            f"Invalid principal values: "
            f"{invalid_principal}"
        )

        self.stdout.write(
            f"Invalid dates: {invalid_dates}"
        )

        total_invalid = (
            invalid_emi
            + invalid_outstanding
            + invalid_principal
            + invalid_dates
        )

        self.stdout.write(
            f"\nTotal invalid loans: {total_invalid}"
        )

        if fix_records:

            self.stdout.write(
                self.style.SUCCESS(
                    f"\nOutstanding amounts fixed: "
                    f"{fixed_records}"
                )
            )

        if total_invalid == 0:

            self.stdout.write(
                self.style.SUCCESS(
                    "\nLOAN DATA VALIDATION PASSED"
                )
            )

        elif fix_records:

            self.stdout.write(
                self.style.WARNING(
                    "\nFIX COMPLETED."
                    "\nRun validation again without "
                    "--fix to confirm."
                )
            )

        else:

            self.stdout.write(
                self.style.ERROR(
                    "\nLOAN DATA HAS VALIDATION ERRORS"
                )
            )