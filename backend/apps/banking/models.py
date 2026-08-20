import uuid

from django.db import models


class BankAccount(models.Model):

    class Meta:
        db_table = "bank_accounts"
        
    class AccountType(models.TextChoices):
        SAVINGS = "SAVINGS", "Savings"
        CURRENT = "CURRENT", "Current"

    class AccountStatus(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        BLOCKED = "BLOCKED", "Blocked"
        CLOSED = "CLOSED", "Closed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    customer = models.ForeignKey(
        "users.Customer",
        on_delete=models.CASCADE,
        related_name="bank_accounts",
    )

    account_number = models.CharField(max_length=30, unique=True)
    account_type = models.CharField(
        max_length=20,
        choices=AccountType.choices,
    )
    currency = models.CharField(max_length=3, default="INR")
    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
    )

    status = models.CharField(
        max_length=20,
        choices=AccountStatus.choices,
        default=AccountStatus.ACTIVE,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.account_number