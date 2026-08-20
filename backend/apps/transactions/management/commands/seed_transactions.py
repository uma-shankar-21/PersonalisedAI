import random
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.users.models import Customer
from apps.banking.models import BankAccount
from apps.loans.models import Loan
from apps.transactions.models import Transaction


TOTAL_TRANSACTIONS_PER_CUSTOMER = 1000
BATCH_SIZE = 5000

START_YEAR = 2020
END_YEAR = 2026


class Command(BaseCommand):
    help = "Generate realistic transaction data for all customers"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing transactions before generating new ones",
        )

    def handle(self, *args, **options):

        if options["clear"]:
            self.stdout.write(
                self.style.WARNING(
                    "Deleting existing transactions..."
                )
            )
            Transaction.objects.all().delete()

        customers = Customer.objects.prefetch_related(
            "bank_accounts",
            "loans",
        ).all()

        total_customers = customers.count()

        self.stdout.write(
            self.style.SUCCESS(
                f"Found {total_customers} customers"
            )
        )

        all_transactions = []
        account_balances = {}

        for index, customer in enumerate(customers, start=1):

            transactions = self.generate_customer_transactions(
                customer
            )

            if len(transactions) != TOTAL_TRANSACTIONS_PER_CUSTOMER:
                raise Exception(
                    f"Customer {customer.id} has "
                    f"{len(transactions)} transactions "
                    f"instead of {TOTAL_TRANSACTIONS_PER_CUSTOMER}"
                )

            all_transactions.extend(transactions)

            if len(all_transactions) >= BATCH_SIZE:

                Transaction.objects.bulk_create(
                    all_transactions,
                    batch_size=BATCH_SIZE,
                )

                self.update_running_balances(
                    all_transactions,
                    account_balances,
                )

                self.stdout.write(
                    f"Inserted {len(all_transactions)} transactions..."
                )

                all_transactions = []

            if index % 50 == 0:
                self.stdout.write(
                    f"Processed {index}/{total_customers} customers"
                )

        if all_transactions:

            Transaction.objects.bulk_create(
                all_transactions,
                batch_size=BATCH_SIZE,
            )

            self.update_running_balances(
                all_transactions,
                account_balances,
            )

        self.update_account_balances(account_balances)

        total_transactions = Transaction.objects.count()

        self.stdout.write(
            self.style.SUCCESS(
                "\nTransaction generation completed"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Total transactions: {total_transactions}"
            )
        )

    # --------------------------------------------------
    # CUSTOMER TRANSACTION GENERATOR
    # --------------------------------------------------

    def generate_customer_transactions(self, customer):

        accounts = list(customer.bank_accounts.all())

        if not accounts:
            return []

        savings_account = next(
            (
                account
                for account in accounts
                if account.account_type == "SAVINGS"
            ),
            accounts[0],
        )

        current_account = next(
            (
                account
                for account in accounts
                if account.account_type == "CURRENT"
            ),
            None,
        )

        customer_loans = list(customer.loans.all())

        salary = self.get_customer_salary()

        transactions = []

        start_date = self.get_start_date(
            accounts
        )

        end_date = timezone.now()

        # ----------------------------------------------
        # 1. MONTHLY RECURRING TRANSACTIONS
        # ----------------------------------------------

        current_date = start_date.replace(day=1)

        while current_date <= end_date:

            year = current_date.year
            month = current_date.month

            # SALARY / MAIN CREDIT

            salary_date = self.random_date_in_month(
                year,
                month,
                1,
                5,
            )

            salary_amount = self.calculate_salary_for_year(
                salary,
                year,
            )

            transactions.append(
                self.create_transaction(
                    account=savings_account,
                    transaction_type="CREDIT",
                    amount=salary_amount,
                    transaction_date=salary_date,
                    category="SALARY",
                    description="Monthly salary credited",
                    merchant="Employer",
                )
            )

            # ------------------------------------------
            # MONTHLY FOOD
            # ------------------------------------------

            food_count = random.randint(4, 10)

            for _ in range(food_count):

                amount = self.random_decimal(
                    150,
                    2500,
                )

                transaction_date = self.random_date_in_month(
                    year,
                    month,
                    1,
                    28,
                )

                transactions.append(
                    self.create_transaction(
                        account=random.choice(accounts),
                        transaction_type="DEBIT",
                        amount=amount,
                        transaction_date=transaction_date,
                        category="FOOD",
                        description=random.choice(
                            [
                                "Restaurant payment",
                                "Food delivery payment",
                                "Cafe and dining expense",
                                "Online food order",
                            ]
                        ),
                        merchant=random.choice(
                            [
                                "Swiggy",
                                "Zomato",
                                "Restaurant",
                                "Cafe",
                            ]
                        ),
                    )
                )

            # ------------------------------------------
            # MONTHLY GROCERIES
            # Total roughly 4K - 7K
            # ------------------------------------------

            grocery_total = self.random_decimal(
                4000,
                7000,
            )

            grocery_transactions = random.randint(2, 4)

            grocery_remaining = grocery_total

            for grocery_index in range(
                grocery_transactions
            ):

                if grocery_index == grocery_transactions - 1:
                    amount = grocery_remaining
                else:

                    amount = (
                        grocery_total
                        / Decimal(grocery_transactions)
                    )

                    variation = self.random_decimal(
                        0.7,
                        1.3,
                    )

                    amount = (
                        amount * variation
                    ).quantize(
                        Decimal("0.01"),
                        rounding=ROUND_HALF_UP,
                    )

                    if amount > grocery_remaining:
                        amount = grocery_remaining

                grocery_remaining -= amount

                transactions.append(
                    self.create_transaction(
                        account=savings_account,
                        transaction_type="DEBIT",
                        amount=amount,
                        transaction_date=self.random_date_in_month(
                            year,
                            month,
                            1,
                            28,
                        ),
                        category="GROCERIES",
                        description="Monthly grocery purchase",
                        merchant=random.choice(
                            [
                                "DMart",
                                "Reliance Fresh",
                                "BigBasket",
                                "Local Supermarket",
                            ]
                        ),
                    )
                )

            # ------------------------------------------
            # UTILITIES
            # ------------------------------------------

            utilities = [
                (
                    "Electricity bill payment",
                    "ELECTRICITY",
                    800,
                    4000,
                ),
                (
                    "Mobile and internet bill",
                    "TELECOM",
                    500,
                    2500,
                ),
                (
                    "Water bill payment",
                    "UTILITIES",
                    200,
                    1000,
                ),
            ]

            for description, category, minimum, maximum in utilities:

                transactions.append(
                    self.create_transaction(
                        account=savings_account,
                        transaction_type="DEBIT",
                        amount=self.random_decimal(
                            minimum,
                            maximum,
                        ),
                        transaction_date=self.random_date_in_month(
                            year,
                            month,
                            5,
                            25,
                        ),
                        category=category,
                        description=description,
                        merchant="Utility Provider",
                    )
                )

            # ------------------------------------------
            # MONTHLY SAVINGS
            # ------------------------------------------

            savings_amount = min(
                self.random_decimal(
                    3000,
                    20000,
                ),
                salary_amount * Decimal("0.25"),
            )

            transactions.append(
                self.create_transaction(
                    account=savings_account,
                    transaction_type="DEBIT",
                    amount=savings_amount,
                    transaction_date=self.random_date_in_month(
                        year,
                        month,
                        10,
                        28,
                    ),
                    category="SAVINGS",
                    description="Monthly savings transfer",
                    merchant="Savings Account",
                )
            )

            # ------------------------------------------
            # LOAN EMI
            # ------------------------------------------

            for loan in customer_loans:

                if not self.loan_should_have_emi(
                    loan,
                    current_date,
                ):
                    continue

                emi_date = self.get_emi_date(
                    loan,
                    year,
                    month,
                )

                transactions.append(
                    self.create_transaction(
                        account=savings_account,
                        transaction_type="DEBIT",
                        amount=loan.monthly_emi,
                        transaction_date=emi_date,
                        category="LOAN_EMI",
                        description=(
                            f"Monthly EMI payment for "
                            f"{loan.loan_type} loan"
                        ),
                        merchant="Bank Loan EMI",
                    )
                )

            # ------------------------------------------
            # TRAVEL
            # ------------------------------------------

            travel_count = random.randint(2, 6)

            for _ in range(travel_count):

                amount = self.random_decimal(
                    100,
                    2000,
                )

                transactions.append(
                    self.create_transaction(
                        account=random.choice(accounts),
                        transaction_type="DEBIT",
                        amount=amount,
                        transaction_date=self.random_date_in_month(
                            year,
                            month,
                            1,
                            28,
                        ),
                        category="TRAVEL",
                        description=random.choice(
                            [
                                "Local transport expense",
                                "Cab booking",
                                "Fuel expense",
                                "Public transport payment",
                            ]
                        ),
                        merchant=random.choice(
                            [
                                "Uber",
                                "Ola",
                                "Fuel Station",
                                "Metro",
                            ]
                        ),
                    )
                )

            # ------------------------------------------
            # SHOPPING EVERY 3-4 MONTHS
            # ------------------------------------------

            if random.random() < 0.30:

                transactions.append(
                    self.create_transaction(
                        account=random.choice(accounts),
                        transaction_type="DEBIT",
                        amount=self.random_decimal(
                            7000,
                            10000,
                        ),
                        transaction_date=self.random_date_in_month(
                            year,
                            month,
                            1,
                            28,
                        ),
                        category="SHOPPING",
                        description="Clothing and personal shopping",
                        merchant=random.choice(
                            [
                                "Amazon",
                                "Flipkart",
                                "Myntra",
                                "Retail Store",
                            ]
                        ),
                    )
                )

            # ------------------------------------------
            # EDUCATION ONCE PER YEAR
            # ------------------------------------------

            if month == random.randint(6, 9):

                years_from_start = year - START_YEAR

                base_fee = self.random_decimal(
                    50000,
                    150000,
                )

                education_fee = (
                    base_fee
                    * (
                        Decimal("1.05")
                        ** years_from_start
                    )
                ).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP,
                )

                transactions.append(
                    self.create_transaction(
                        account=savings_account,
                        transaction_type="DEBIT",
                        amount=education_fee,
                        transaction_date=self.random_date_in_month(
                            year,
                            month,
                            1,
                            15,
                        ),
                        category="EDUCATION",
                        description="Annual education fee payment",
                        merchant="School or College",
                    )
                )

            # ------------------------------------------
            # INSURANCE
            # ------------------------------------------

            if month == random.randint(1, 12):

                transactions.append(
                    self.create_transaction(
                        account=savings_account,
                        transaction_type="DEBIT",
                        amount=self.random_decimal(
                            5000,
                            50000,
                        ),
                        transaction_date=self.random_date_in_month(
                            year,
                            month,
                            1,
                            28,
                        ),
                        category="INSURANCE",
                        description="Insurance premium payment",
                        merchant="Insurance Provider",
                    )
                )

            current_date = self.next_month(
                current_date
            )

        # ----------------------------------------------
        # 2. ELECTRONICS
        # Every 3-4 years approximately
        # ----------------------------------------------

        years_available = max(
            1,
            end_date.year - start_date.year + 1,
        )

        electronics_count = max(
            1,
            years_available // random.randint(3, 4),
        )

        for _ in range(electronics_count):

            transaction_date = self.random_date_between(
                start_date,
                end_date,
            )

            category = random.choice(
                [
                    "ELECTRONICS",
                    "ELECTRONICS",
                    "ELECTRONICS",
                ]
            )

            product = random.choice(
                [
                    "Smartphone",
                    "Laptop",
                    "Tablet",
                ]
            )

            amount = self.random_decimal(
                30000,
                100000,
            )

            transactions.append(
                self.create_transaction(
                    account=random.choice(accounts),
                    transaction_type="DEBIT",
                    amount=amount,
                    transaction_date=transaction_date,
                    category=category,
                    description=f"{product} purchase",
                    merchant=random.choice(
                        [
                            "Apple Store",
                            "Samsung",
                            "Croma",
                            "Reliance Digital",
                            "Amazon",
                            "Flipkart",
                        ]
                    ),
                )
            )

        # ----------------------------------------------
        # 3. FILL REMAINING TRANSACTIONS
        # ----------------------------------------------

        remaining = (
            TOTAL_TRANSACTIONS_PER_CUSTOMER
            - len(transactions)
        )

        if remaining > 0:

            transactions.extend(
                self.generate_additional_transactions(
                    accounts=accounts,
                    count=remaining,
                    start_date=start_date,
                    end_date=end_date,
                )
            )

        # ----------------------------------------------
        # 4. IF MORE THAN 1000, RANDOMLY REDUCE
        # ----------------------------------------------

        if len(transactions) > TOTAL_TRANSACTIONS_PER_CUSTOMER:

            transactions = random.sample(
                transactions,
                TOTAL_TRANSACTIONS_PER_CUSTOMER,
            )

        return transactions

    # --------------------------------------------------
    # ADDITIONAL REALISTIC TRANSACTIONS
    # --------------------------------------------------

    def generate_additional_transactions(
        self,
        accounts,
        count,
        start_date,
        end_date,
    ):

        transactions = []

        transaction_templates = [
            (
                "FOOD",
                100,
                2000,
                "Food and dining payment",
                "Restaurant",
            ),
            (
                "GROCERIES",
                500,
                5000,
                "Grocery purchase",
                "Supermarket",
            ),
            (
                "TRAVEL",
                100,
                3000,
                "Travel expense",
                "Travel Service",
            ),
            (
                "ENTERTAINMENT",
                200,
                5000,
                "Entertainment expense",
                "Entertainment",
            ),
            (
                "HEALTHCARE",
                500,
                15000,
                "Medical expense",
                "Healthcare Provider",
            ),
            (
                "TRANSFER",
                500,
                25000,
                "Bank transfer",
                "Bank Transfer",
            ),
            (
                "SHOPPING",
                500,
                10000,
                "Online shopping payment",
                "Online Store",
            ),
        ]

        for _ in range(count):

            (
                category,
                minimum,
                maximum,
                description,
                merchant,
            ) = random.choice(
                transaction_templates
            )

            transactions.append(
                self.create_transaction(
                    account=random.choice(accounts),
                    transaction_type="DEBIT",
                    amount=self.random_decimal(
                        minimum,
                        maximum,
                    ),
                    transaction_date=self.random_date_between(
                        start_date,
                        end_date,
                    ),
                    category=category,
                    description=description,
                    merchant=merchant,
                )
            )

        return transactions

    # --------------------------------------------------
    # HELPER METHODS
    # --------------------------------------------------

    def create_transaction(
        self,
        account,
        transaction_type,
        amount,
        transaction_date,
        category,
        description,
        merchant,
    ):

        return Transaction(
            account=account,
            transaction_type=transaction_type,
            amount=Decimal(amount).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            ),
            currency="INR",
            description=description,
            merchant=merchant,
            transaction_date=transaction_date,
            category=category,
            status="COMPLETED",
        )

    def get_customer_salary(self):

        return self.random_decimal(
            40000,
            200000,
        )

    def calculate_salary_for_year(
        self,
        base_salary,
        year,
    ):

        growth_years = year - START_YEAR

        growth_factor = (
            Decimal("1.07")
            ** growth_years
        )

        return (
            base_salary
            * growth_factor
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    def get_start_date(self, accounts):

        earliest_account = min(
            account.created_at
            for account in accounts
        )

        start = earliest_account

        minimum_start = timezone.make_aware(
            datetime(START_YEAR, 1, 1)
        )

        if start < minimum_start:
            start = minimum_start

        return start

    def loan_should_have_emi(
        self,
        loan,
        current_date,
    ):

        loan_start = loan.created_at

        if current_date < loan_start:
            return False

        if loan.status == "COMPLETED":

            payment_months = loan.tenure_years * 12

            completion_date = (
                loan_start
                + timedelta(
                    days=payment_months * 30
                )
            )

            if current_date > completion_date:
                return False

        return True

    def get_emi_date(
        self,
        loan,
        year,
        month,
    ):

        due_day = random.randint(3, 10)

        return self.random_date_in_month(
            year,
            month,
            due_day,
            due_day,
        )

    def random_decimal(
        self,
        minimum,
        maximum,
    ):

        value = random.uniform(
            float(minimum),
            float(maximum),
        )

        return Decimal(
            str(round(value, 2))
        )

    def random_date_in_month(
        self,
        year,
        month,
        start_day,
        end_day,
    ):

        day = random.randint(
            start_day,
            min(end_day, 28),
        )

        naive_datetime = datetime(
            year,
            month,
            day,
            random.randint(8, 22),
            random.randint(0, 59),
            random.randint(0, 59),
        )

        return timezone.make_aware(
            naive_datetime
        )

    def random_date_between(
        self,
        start_date,
        end_date,
    ):

        delta = end_date - start_date

        random_seconds = random.randint(
            0,
            int(delta.total_seconds()),
        )

        return start_date + timedelta(
            seconds=random_seconds
        )

    def next_month(self, date):

        if date.month == 12:
            return date.replace(
                year=date.year + 1,
                month=1,
            )

        return date.replace(
            month=date.month + 1
        )

    # --------------------------------------------------
    # BALANCE CALCULATION
    # --------------------------------------------------

    def update_running_balances(
        self,
        transactions,
        account_balances,
    ):

        for transaction_item in transactions:

            account_id = transaction_item.account_id

            if account_id not in account_balances:
                account_balances[
                    account_id
                ] = Decimal("0.00")

            if transaction_item.transaction_type == "CREDIT":

                account_balances[
                    account_id
                ] += transaction_item.amount

            else:

                account_balances[
                    account_id
                ] -= transaction_item.amount

    def update_account_balances(
        self,
        account_balances,
    ):

        accounts = BankAccount.objects.filter(
            id__in=account_balances.keys()
        )

        for account in accounts:

            calculated_balance = account_balances.get(
                account.id,
                Decimal("0.00"),
            )

            # Avoid unrealistic negative balances
            if calculated_balance < Decimal("100.00"):

                calculated_balance = self.random_decimal(
                    500,
                    50000,
                )

            account.balance = calculated_balance

        BankAccount.objects.bulk_update(
            list(accounts),
            ["balance"],
            batch_size=1000,
        )