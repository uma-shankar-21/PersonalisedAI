from decimal import Decimal, ROUND_HALF_UP

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.loans.models import Loan


class Command(BaseCommand):

    help = (
        "Validate loan EMI, total payable, elapsed months, "
        "remaining months and outstanding amount"
    )

    def handle(self, *args, **options):

        loans = Loan.objects.all().order_by("created_at")

        now = timezone.now()

        self.stdout.write("")
        self.stdout.write("=" * 100)
        self.stdout.write(
            f"VALIDATING {loans.count()} LOANS"
        )
        self.stdout.write("=" * 100)

        invalid_emi = 0
        invalid_outstanding = 0
        invalid_principal = 0
        invalid_dates = 0
        valid_loans = 0

        for loan in loans.iterator():

            result = self.validate_loan(
                loan=loan,
                now=now,
            )

            errors = result["errors"]

            if not errors:

                valid_loans += 1
                continue

            self.stdout.write("")
            self.stdout.write(
                self.style.ERROR(
                    f"INVALID LOAN: {loan.id}"
                )
            )

            self.stdout.write(
                f"Customer ID: {loan.customer_id}"
            )

            self.stdout.write(
                f"Loan Type: {loan.loan_type}"
            )

            self.stdout.write(
                f"Status: {loan.status}"
            )

            self.stdout.write(
                f"Loan Start: {loan.created_at}"
            )

            self.stdout.write(
                f"Principal: {loan.principal_amount}"
            )

            self.stdout.write(
                f"Interest Rate: {loan.interest_rate}%"
            )

            self.stdout.write(
                f"Tenure: {loan.tenure_years} years"
            )

            self.stdout.write(
                f"Total Months: {result['total_months']}"
            )

            self.stdout.write(
                f"Elapsed Months: {result['elapsed_months']}"
            )

            self.stdout.write(
                f"Remaining Months: {result['remaining_months']}"
            )

            self.stdout.write(
                f"Stored EMI: {loan.monthly_emi}"
            )

            self.stdout.write(
                f"Expected EMI: {result['expected_emi']}"
            )

            self.stdout.write(
                f"Stored Outstanding: "
                f"{loan.outstanding_amount}"
            )

            self.stdout.write(
                f"Expected Outstanding: "
                f"{result['expected_outstanding']}"
            )

            self.stdout.write(
                self.style.ERROR(
                    "Errors:"
                )
            )

            for error in errors:

                self.stdout.write(
                    f"  - {error}"
                )

            if result["emi_invalid"]:
                invalid_emi += 1

            if result["outstanding_invalid"]:
                invalid_outstanding += 1

            if result["principal_invalid"]:
                invalid_principal += 1

            if result["date_invalid"]:
                invalid_dates += 1

        self.stdout.write("")
        self.stdout.write("=" * 100)
        self.stdout.write("VALIDATION SUMMARY")
        self.stdout.write("=" * 100)

        self.stdout.write(
            f"Total loans: {loans.count()}"
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Valid loans: {valid_loans}"
            )
        )

        self.stdout.write(
            self.style.ERROR(
                f"Invalid EMI calculations: {invalid_emi}"
            )
        )

        self.stdout.write(
            self.style.ERROR(
                f"Invalid outstanding amounts: "
                f"{invalid_outstanding}"
            )
        )

        self.stdout.write(
            self.style.ERROR(
                f"Invalid principal values: "
                f"{invalid_principal}"
            )
        )

        self.stdout.write(
            self.style.ERROR(
                f"Invalid dates: {invalid_dates}"
            )
        )

        total_invalid = (
            loans.count() - valid_loans
        )

        self.stdout.write("")
        self.stdout.write(
            f"Total invalid loans: {total_invalid}"
        )

        if total_invalid == 0:

            self.stdout.write(
                self.style.SUCCESS(
                    "ALL LOANS PASSED VALIDATION"
                )
            )

        else:

            self.stdout.write(
                self.style.ERROR(
                    "LOAN DATA HAS VALIDATION ERRORS"
                )
            )

    def validate_loan(
        self,
        loan,
        now,
    ):

        errors = []

        emi_invalid = False
        outstanding_invalid = False
        principal_invalid = False
        date_invalid = False

        # --------------------------------------------------
        # BASIC PRINCIPAL VALIDATION
        # --------------------------------------------------

        if loan.principal_amount <= 0:

            principal_invalid = True

            errors.append(
                "Principal amount must be greater than zero"
            )

        # --------------------------------------------------
        # DATE VALIDATION
        # --------------------------------------------------

        if loan.created_at > now:

            date_invalid = True

            errors.append(
                "Loan start date is in the future"
            )

        # --------------------------------------------------
        # TOTAL LOAN MONTHS
        # --------------------------------------------------

        total_months = (
            loan.tenure_years * 12
        )

        if total_months <= 0:

            date_invalid = True

            errors.append(
                "Invalid loan tenure"
            )

            return {
                "errors": errors,
                "emi_invalid": emi_invalid,
                "outstanding_invalid": outstanding_invalid,
                "principal_invalid": principal_invalid,
                "date_invalid": date_invalid,
                "expected_emi": Decimal("0.00"),
                "expected_outstanding": Decimal("0.00"),
                "total_months": 0,
                "elapsed_months": 0,
                "remaining_months": 0,
            }

        # --------------------------------------------------
        # SIMPLE INTEREST CALCULATION
        #
        # SI = P × R × T / 100
        # --------------------------------------------------

        simple_interest = (
            loan.principal_amount
            * loan.interest_rate
            * Decimal(loan.tenure_years)
            / Decimal("100")
        )

        total_payable = (
            loan.principal_amount
            + simple_interest
        )

        expected_emi = (
            total_payable
            / Decimal(total_months)
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        # --------------------------------------------------
        # EMI VALIDATION
        # --------------------------------------------------

        emi_difference = abs(
            loan.monthly_emi
            - expected_emi
        )

        if emi_difference > Decimal("0.01"):

            emi_invalid = True

            errors.append(
                "Monthly EMI does not match "
                "simple interest calculation"
            )

        # --------------------------------------------------
        # CALCULATE ELAPSED MONTHS
        #
        # This uses calendar months instead of dividing
        # total days by 30.
        # --------------------------------------------------

        elapsed_months = (
            (now.year - loan.created_at.year)
            * 12
            + (
                now.month
                - loan.created_at.month
            )
        )

        # Current month is not completed yet if today's
        # day is before the loan start day.
        if now.day < loan.created_at.day:

            elapsed_months -= 1

        elapsed_months = max(
            elapsed_months,
            0,
        )

        # Loan cannot have more elapsed months
        # than its full tenure.
        elapsed_months = min(
            elapsed_months,
            total_months,
        )

        remaining_months = (
            total_months
            - elapsed_months
        )

        remaining_months = max(
            remaining_months,
            0,
        )

        # --------------------------------------------------
        # EXPECTED OUTSTANDING
        #
        # Outstanding = Remaining EMIs × Monthly EMI
        # --------------------------------------------------

        expected_outstanding = (
            expected_emi
            * remaining_months
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        outstanding_difference = abs(
            loan.outstanding_amount
            - expected_outstanding
        )

        if outstanding_difference > Decimal("1.00"):

            outstanding_invalid = True

            errors.append(
                "Outstanding amount does not match "
                "remaining tenure"
            )

        # --------------------------------------------------
        # STATUS VALIDATION
        # --------------------------------------------------

        if (
            loan.status == "ABOUT_TO_CLOSE"
            and remaining_months > 6
        ):

            errors.append(
                "ABOUT_TO_CLOSE loan has more than "
                "6 months remaining"
            )

        if (
            loan.status == "ABOUT_TO_CLOSE"
            and remaining_months == 0
        ):

            errors.append(
                "ABOUT_TO_CLOSE loan has already "
                "completed its tenure"
            )

        if (
            remaining_months == 0
            and loan.outstanding_amount > Decimal("1.00")
        ):

            errors.append(
                "Loan tenure completed but outstanding "
                "amount is not zero"
            )

        return {
            "errors": errors,
            "emi_invalid": emi_invalid,
            "outstanding_invalid": outstanding_invalid,
            "principal_invalid": principal_invalid,
            "date_invalid": date_invalid,
            "expected_emi": expected_emi,
            "expected_outstanding": expected_outstanding,
            "total_months": total_months,
            "elapsed_months": elapsed_months,
            "remaining_months": remaining_months,
        }