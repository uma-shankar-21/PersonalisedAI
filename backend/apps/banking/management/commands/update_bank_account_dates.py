import random
from datetime import datetime, date, time, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.banking.models import BankAccount


class Command(BaseCommand):

    help = (
        "Update existing bank account opening dates with "
        "unique random dates between 2020 and the current date"
    )

    START_DATE = date(2020, 1, 1)

    def handle(self, *args, **options):

        random.seed(20260820)

        accounts = list(
            BankAccount.objects.all()
            .select_related("customer")
            .order_by("id")
        )

        total_accounts = len(accounts)

        if total_accounts == 0:
            self.stdout.write(
                self.style.ERROR(
                    "No bank accounts found."
                )
            )
            return

        as_of_date = timezone.localdate()

        total_days = (
            as_of_date - self.START_DATE
        ).days + 1

        if total_accounts > total_days:
            self.stdout.write(
                self.style.ERROR(
                    f"Cannot generate {total_accounts} unique dates. "
                    f"Only {total_days} dates are available."
                )
            )
            return

        self.stdout.write(
            f"Bank accounts found: {total_accounts}"
        )

        self.stdout.write(
            f"Date range: "
            f"{self.START_DATE} -> {as_of_date}"
        )

        # Generate unique day offsets.
        #
        # random.sample guarantees that no two accounts
        # receive the same calendar date.
        day_offsets = random.sample(
            range(total_days),
            total_accounts,
        )

        updates = []

        with transaction.atomic():

            for account, day_offset in zip(
                accounts,
                day_offsets,
            ):

                opening_date = (
                    self.START_DATE
                    + timedelta(days=day_offset)
                )

                # Generate a random time.
                hour = random.randint(0, 23)
                minute = random.randint(0, 59)
                second = random.randint(0, 59)

                naive_datetime = datetime.combine(
                    opening_date,
                    time(
                        hour=hour,
                        minute=minute,
                        second=second,
                    ),
                )

                # Make timezone-aware datetime because Django
                # is using timezone support.
                created_at = timezone.make_aware(
                    naive_datetime,
                    timezone.get_current_timezone(),
                )

                # Safety: account date should never be in future.
                if created_at > timezone.now():
                    created_at = timezone.now() - timedelta(
                        seconds=random.randint(1, 60)
                    )

                account.created_at = created_at

                # Keep updated_at aligned for this historical
                # seed-data correction.
                account.updated_at = created_at

                updates.append(account)

            BankAccount.objects.bulk_update(
                updates,
                [
                    "created_at",
                    "updated_at",
                ],
                batch_size=500,
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully updated "
                f"{len(updates)} bank accounts."
            )
        )

        self.validate()

    def validate(self):

        self.stdout.write("")
        self.stdout.write(
            "========== VALIDATION =========="
        )

        accounts = BankAccount.objects.all()

        total_accounts = accounts.count()

        # Count unique calendar dates.
        unique_dates = set(
            account.created_at.date()
            for account in accounts.iterator()
        )

        oldest_account = (
            accounts
            .order_by("created_at")
            .first()
        )

        newest_account = (
            accounts
            .order_by("-created_at")
            .first()
        )

        invalid_old_dates = accounts.filter(
            created_at__date__lt=self.START_DATE
        ).count()

        future_dates = accounts.filter(
            created_at__gt=timezone.now()
        ).count()

        duplicate_dates = (
            total_accounts
            - len(unique_dates)
        )

        self.stdout.write(
            f"Total accounts: {total_accounts}"
        )

        self.stdout.write(
            f"Unique opening dates: "
            f"{len(unique_dates)}"
        )

        self.stdout.write(
            f"Duplicate opening dates: "
            f"{duplicate_dates}"
        )

        self.stdout.write(
            f"Dates before 2020: "
            f"{invalid_old_dates}"
        )

        self.stdout.write(
            f"Future dates: "
            f"{future_dates}"
        )

        if oldest_account:
            self.stdout.write(
                f"Oldest account date: "
                f"{oldest_account.created_at}"
            )

        if newest_account:
            self.stdout.write(
                f"Newest account date: "
                f"{newest_account.created_at}"
            )

        if (
            duplicate_dates == 0
            and invalid_old_dates == 0
            and future_dates == 0
        ):

            self.stdout.write(
                self.style.SUCCESS(
                    "VALIDATION PASSED"
                )
            )

        else:

            self.stdout.write(
                self.style.ERROR(
                    "VALIDATION FAILED"
                )
            )