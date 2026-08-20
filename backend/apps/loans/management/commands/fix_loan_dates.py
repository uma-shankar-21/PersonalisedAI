import random
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.loans.models import Loan


class Command(BaseCommand):
    help = "Fix existing loan dates based on tenure and loan status"

    def handle(self, *args, **options):

        random.seed(20260820)

        as_of_datetime = timezone.now()
        as_of_date = as_of_datetime.date()

        loans = Loan.objects.all()

        total_loans = loans.count()

        if total_loans == 0:
            self.stdout.write(
                self.style.ERROR(
                    "No loans found."
                )
            )
            return

        updated = 0

        for loan in loans:

            total_months = loan.tenure_years * 12

            elapsed_months = self.get_elapsed_months(
                total_months=total_months,
                status=loan.status,
            )

            # Loan start date must always be in the past.
            days_since_start = (
                elapsed_months * 30
                + random.randint(0, 29)
            )

            created_at = (
                as_of_datetime
                - timedelta(days=days_since_start)
            )

            # Extra safety: never allow future date.
            if created_at >= as_of_datetime:
                created_at = (
                    as_of_datetime
                    - timedelta(days=random.randint(1, 30))
                )

            remaining_months = (
                total_months - elapsed_months
            )

            # Outstanding amount based on remaining EMIs.
            outstanding_amount = (
                loan.monthly_emi
                * Decimal(remaining_months)
            ).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )

            # Next EMI due date.
            if loan.status == Loan.LoanStatus.PENDING:

                next_due_date = (
                    as_of_date
                    + timedelta(
                        days=random.randint(5, 30)
                    )
                )

            else:

                next_due_date = (
                    as_of_date
                    + timedelta(
                        days=random.randint(1, 30)
                    )
                )

            Loan.objects.filter(
                id=loan.id
            ).update(
                created_at=created_at,
                updated_at=as_of_datetime,
                outstanding_amount=outstanding_amount,
                next_due_date=next_due_date,
            )

            updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully updated {updated} loans."
            )
        )

        self.print_summary(
            as_of_datetime
        )

    @staticmethod
    def get_elapsed_months(
        total_months,
        status,
    ):

        if status == Loan.LoanStatus.PENDING:

            # Very recently created loan.
            # No EMI or only very few EMIs completed.
            return random.randint(
                0,
                min(2, total_months - 1)
            )

        if status == Loan.LoanStatus.ABOUT_TO_CLOSE:

            # Only 1 to 6 months remaining.
            remaining_months = random.randint(1, 6)

            return (
                total_months
                - remaining_months
            )

        if status == Loan.LoanStatus.OPEN:

            # OPEN loan can be at any realistic stage,
            # but it cannot already be about to close.
            #
            # At least 7 months must remain.
            maximum_elapsed = (
                total_months - 7
            )

            # For a very new loan,
            # at least 1 EMI period may have elapsed.
            minimum_elapsed = 1

            if maximum_elapsed <= minimum_elapsed:
                return minimum_elapsed

            return random.randint(
                minimum_elapsed,
                maximum_elapsed,
            )

        # Fallback.
        return random.randint(
            1,
            max(1, total_months - 7),
        )

    def print_summary(
        self,
        as_of_datetime,
    ):

        self.stdout.write("")
        self.stdout.write(
            "========== LOAN DATE SUMMARY =========="
        )

        self.stdout.write(
            f"As of date: {as_of_datetime}"
        )

        for status in [
            Loan.LoanStatus.OPEN,
            Loan.LoanStatus.PENDING,
            Loan.LoanStatus.ABOUT_TO_CLOSE,
        ]:

            loans = Loan.objects.filter(
                status=status
            )

            self.stdout.write(
                f"\n{status}: {loans.count()} loans"
            )

            sample = loans.order_by(
                "created_at"
            ).first()

            if sample:

                self.stdout.write(
                    f"Sample created_at: "
                    f"{sample.created_at}"
                )

        future_loans = Loan.objects.filter(
            created_at__gt=as_of_datetime
        ).count()

        self.stdout.write("")
        self.stdout.write(
            f"Future dated loans: {future_loans}"
        )

        if future_loans == 0:

            self.stdout.write(
                self.style.SUCCESS(
                    "Validation passed: "
                    "No loans have future created_at dates."
                )
            )