import random
import uuid
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.loans.models import Loan
from apps.users.models import Customer


class Command(BaseCommand):
    help = "Generate realistic loan records for 850 customers"

    TOTAL_LOANS = 850

    def handle(self, *args, **options):
        random.seed(20260819)

        customers = list(
            Customer.objects.filter(is_active=True)
        )

        if len(customers) < self.TOTAL_LOANS:
            self.stdout.write(
                self.style.ERROR(
                    f"Need at least {self.TOTAL_LOANS} customers. "
                    f"Found {len(customers)}."
                )
            )
            return

        if Loan.objects.exists():
            self.stdout.write(
                self.style.ERROR(
                    "Loans already exist. "
                    "Delete existing loan data before running this seed."
                )
            )
            return

        selected_customers = random.sample(
            customers,
            self.TOTAL_LOANS,
        )

        # Approximately 95% ACTIVE and 5% split between
        # PENDING and ABOUT_TO_CLOSE.
        statuses = (
            ["ACTIVE"] * 808
            + ["PENDING"] * 21
            + ["ABOUT_TO_CLOSE"] * 21
        )

        random.shuffle(statuses)

        # 50% from CAR/BIKE/GOLD and 50% from
        # HOME/PERSONAL/BUSINESS.
        loan_types = (
            ["CAR"] * 142
            + ["BIKE"] * 142
            + ["GOLD"] * 141
            + ["HOME"] * 142
            + ["PERSONAL"] * 142
            + ["BUSINESS"] * 141
        )

        random.shuffle(loan_types)

        created = 0

        with transaction.atomic():

            for customer, status, loan_type in zip(
                selected_customers,
                statuses,
                loan_types,
            ):

                principal = self.generate_principal(loan_type)

                tenure = self.generate_tenure(
                    principal,
                    loan_type,
                )

                interest_rate = Decimal(
                    str(
                        round(
                            random.uniform(14.00, 24.00),
                            2,
                        )
                    )
                )

                # Determine how much of the tenure has elapsed.
                elapsed_months = self.generate_elapsed_months(
                    tenure,
                    status,
                )

                total_months = tenure * 12

                monthly_emi = self.calculate_simple_interest_emi(
                    principal,
                    interest_rate,
                    tenure,
                )

                total_payable = (
                    monthly_emi * total_months
                ).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP,
                )

                if status == "ABOUT_TO_CLOSE":
                    remaining_months = random.randint(1, 6)

                    elapsed_months = (
                        total_months - remaining_months
                    )

                    outstanding_amount = (
                        monthly_emi * remaining_months
                    ).quantize(
                        Decimal("0.01"),
                        rounding=ROUND_HALF_UP,
                    )

                else:
                    outstanding_months = max(
                        total_months - elapsed_months,
                        1,
                    )

                    outstanding_amount = (
                        monthly_emi * outstanding_months
                    ).quantize(
                        Decimal("0.01"),
                        rounding=ROUND_HALF_UP,
                    )

                created_at = (
                    timezone.now()
                    - timedelta(
                        days=elapsed_months * 30
                        + random.randint(0, 29)
                    )
                )

                next_due_date = (
                    timezone.now().date()
                    + timedelta(
                        days=random.randint(1, 30)
                    )
                )

                Loan.objects.create(
                    id=uuid.uuid4(),
                    customer=customer,
                    loan_type=loan_type,
                    principal_amount=principal,
                    outstanding_amount=outstanding_amount,
                    interest_rate=interest_rate,
                    monthly_emi=monthly_emi,
                    tenure_years=tenure,
                    next_due_date=next_due_date,
                    status=status,
                    created_at=created_at,
                    updated_at=created_at,
                )

                created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Loans created: {created}"
            )
        )

        self.print_summary()

    @staticmethod
    def generate_principal(loan_type):

        ranges = {
            "GOLD": (180000, 1000000),
            "BIKE": (180000, 500000),
            "PERSONAL": (200000, 1500000),
            "CAR": (500000, 2500000),
            "BUSINESS": (500000, 4000000),
            "HOME": (1500000, 4000000),
        }

        minimum, maximum = ranges[loan_type]

        amount = random.randint(
            minimum,
            maximum,
        )

        # Keep realistic non-round principal amounts.
        amount = (
            amount // 100
        ) * 100 + random.randint(1, 99)

        return Decimal(amount).quantize(
            Decimal("0.01")
        )

    @staticmethod
    def generate_tenure(principal, loan_type):

        amount = float(principal)

        if loan_type == "BIKE":
            return random.randint(3, 5)

        if loan_type == "GOLD":
            return random.randint(3, 7)

        if loan_type == "PERSONAL":
            return random.randint(3, 7)

        if loan_type == "CAR":
            return random.randint(3, 8)

        if loan_type == "BUSINESS":
            return random.randint(5, 15)

        if loan_type == "HOME":

            if amount <= 2000000:
                return random.randint(7, 15)

            if amount <= 3000000:
                return random.randint(10, 20)

            return random.randint(12, 25)

        return random.randint(3, 10)

    @staticmethod
    def calculate_simple_interest_emi(
        principal,
        interest_rate,
        tenure_years,
    ):

        simple_interest = (
            principal
            * interest_rate
            * Decimal(tenure_years)
            / Decimal("100")
        )

        total_payable = (
            principal + simple_interest
        )

        total_months = tenure_years * 12

        return (
            total_payable / Decimal(total_months)
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    @staticmethod
    def generate_elapsed_months(
        tenure_years,
        status,
    ):

        total_months = tenure_years * 12

        if status == "ABOUT_TO_CLOSE":
            return total_months - random.randint(1, 6)

        # Active loans can be anywhere from
        # early stage to middle/late stage.
        return random.randint(
            1,
            max(1, total_months - 7),
        )

    @staticmethod
    def print_summary():

        from django.db.models import Count

        summary = (
            Loan.objects
            .values("status")
            .annotate(count=Count("id"))
            .order_by("status")
        )

        for item in summary:
            print(
                f"{item['status']}: "
                f"{item['count']}"
            )

        print(
            f"Total loans: {Loan.objects.count()}"
        )