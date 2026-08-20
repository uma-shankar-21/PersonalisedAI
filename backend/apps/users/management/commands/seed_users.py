import uuid

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from faker import Faker

from apps.users.models import Customer


class Command(BaseCommand):
    help = "Create 1,000 unique banking customers"

    TOTAL_USERS = 1000

    def handle(self, *args, **options):
        fake = Faker("en_IN")
        Faker.seed(20260819)

        created_count = 0
        skipped_count = 0

        for _ in range(self.TOTAL_USERS):
            first_name = fake.first_name()
            last_name = fake.last_name()

            username = self.generate_unique_username(
                first_name,
                last_name,
            )

            email = self.generate_unique_email(
                first_name,
                last_name,
                username,
            )

            phone = self.generate_unique_phone()

            user = User.objects.filter(
                username=username
            ).first()

            if user:
                skipped_count += 1
                continue

            user = User.objects.create_user(
                username=username,
                email=email,
                password="Banking@123",
            )

            Customer.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                date_of_birth=fake.date_of_birth(
                    minimum_age=21,
                    maximum_age=70,
                ),
                is_active=True,
            )

            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Users created: {created_count}"
            )
        )

        self.stdout.write(
            self.style.WARNING(
                f"Users skipped: {skipped_count}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Total customers: {Customer.objects.count()}"
            )
        )

    @staticmethod
    def generate_unique_username(first_name, last_name):
        base = (
            f"{first_name.lower()}."
            f"{last_name.lower()}"
        )

        username = base

        while User.objects.filter(username=username).exists():
            username = f"{base}.{uuid.uuid4().hex[:6]}"

        return username

    @staticmethod
    def generate_unique_email(
        first_name,
        last_name,
        username,
    ):
        email = f"{username}@example.com"

        while User.objects.filter(email=email).exists():
            email = (
                f"{first_name.lower()}."
                f"{last_name.lower()}."
                f"{uuid.uuid4().hex[:6]}"
                "@example.com"
            )

        return email

    @staticmethod
    def generate_unique_phone():
        while True:
            phone = f"9{uuid.uuid4().int % 10**9:09d}"

            if not Customer.objects.filter(phone=phone).exists():
                return phone