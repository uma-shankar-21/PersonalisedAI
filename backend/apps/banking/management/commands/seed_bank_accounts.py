import random
import uuid
from datetime import datetime, time

from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker

from apps.banking.models import BankAccount
from apps.users.models import Customer


class Command(BaseCommand):
    help = "Create bank accounts for customers"

    TOTAL_ACCOUNTS = 1500
    CURRENT_ACCOUNT_CUSTOMERS = 500

    def handle(self, *args, **options):
        fake = Faker("en_IN")
        Faker.seed(20260819)
        random.seed(20260819)

        customers = list(
            Customer.objects.filter(is_active=True)
        )

        if len(customers) < 1000:
            self.stdout.write(
                self.style.ERROR(
                    f"Expected at least 1000 customers, "
                    f"found {len(customers)}."
                )
            )
            return

        # Use exactly 1000 customers for this seed.
        customers = customers[:1000]

        # Randomly select 500 customers who get current + savings.
        current_account_customers = set(
            random.sample(
                customers,
                self.CURRENT_ACCOUNT_CUSTOMERS,
            )
        )

        created_count = 0

        with transaction.atomic():

            for customer in customers:

                # Every customer gets a savings account.
                self.create_account(
                    customer=customer,
                    account_type=BankAccount.AccountType.SAVINGS,
                )

                created_count += 1

                # Selected 500 customers also get current account.
                if customer in current_account_customers:
                    self.create_account(
                        customer=customer,
                        account_type=BankAccount.AccountType.CURRENT,
                    )

                    created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Bank accounts created: {created_count}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Total bank accounts: {BankAccount.objects.count()}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Savings accounts: "
                f"{BankAccount.objects.filter(account_type='SAVINGS').count()}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Current accounts: "
                f"{BankAccount.objects.filter(account_type='CURRENT').count()}"
            )
        )

    def create_account(self, customer, account_type):

        account_number = self.generate_account_number()

        balance = self.generate_unique_balance()

        created_at = self.random_created_at()

        BankAccount.objects.create(
            customer=customer,
            account_number=account_number,
            account_type=account_type,
            currency="INR",
            balance=balance,
            status=BankAccount.AccountStatus.ACTIVE,
            created_at=created_at,
            updated_at=created_at,
        )

    @staticmethod
    def generate_account_number():

        while True:
            account_number = str(
                random.randint(
                    100000000000,
                    999999999999,
                )
            )

            if not BankAccount.objects.filter(
                account_number=account_number
            ).exists():
                return account_number

    @staticmethod
    def random_created_at():

        year = random.randint(2020, 2026)
        month = random.randint(1, 12)

        # Avoid generating future dates in 2026.
        if year == 2026:
            month = random.randint(1, 8)

        day = random.randint(1, 28)

        return datetime.combine(
            datetime(year, month, day).date(),
            time(
                random.randint(0, 23),
                random.randint(0, 59),
                random.randint(0, 59),
            ),
        )

    @staticmethod
    def generate_unique_balance():

        while True:
            balance = round(
                random.uniform(5.01, 500000.00),
                2,
            )

            if not BankAccount.objects.filter(
                balance=balance
            ).exists():
                return balance