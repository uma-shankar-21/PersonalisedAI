# apps/transactions/management/commands/fix_invalid_emi.py

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.transactions.models import Transaction


class Command(BaseCommand):

    help = "Delete EMI transactions created before account opening date"

    def handle(self, *args, **options):

        invalid_transactions = []

        emi_transactions = (
            Transaction.objects
            .filter(category="EMI")
            .select_related("account")
        )

        for txn in emi_transactions.iterator():

            if txn.transaction_date < txn.account.created_at:
                invalid_transactions.append(txn.id)

        self.stdout.write(
            f"Invalid EMI transactions found: "
            f"{len(invalid_transactions)}"
        )

        if not invalid_transactions:
            self.stdout.write(
                self.style.SUCCESS(
                    "No invalid EMI transactions found."
                )
            )
            return

        with transaction.atomic():

            deleted_count, _ = (
                Transaction.objects.filter(
                    id__in=invalid_transactions
                ).delete()
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted EMI transactions: {deleted_count}"
            )
        )

        remaining_invalid = 0

        for txn in (
            Transaction.objects
            .filter(category="EMI")
            .select_related("account")
            .iterator()
        ):
            if txn.transaction_date < txn.account.created_at:
                remaining_invalid += 1

        self.stdout.write("")
        self.stdout.write("========== VALIDATION ==========")

        self.stdout.write(
            f"Remaining invalid EMI transactions: "
            f"{remaining_invalid}"
        )

        if remaining_invalid == 0:
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