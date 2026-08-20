import uuid

from django.db import models


class Reward(models.Model):

    class RewardType(models.TextChoices):
        CASHBACK = "CASHBACK", "Cashback"
        POINTS = "POINTS", "Points"
        DISCOUNT = "DISCOUNT", "Discount"

    class RewardStatus(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        USED = "USED", "Used"
        EXPIRED = "EXPIRED", "Expired"

    class Meta:
        db_table = "rewards"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    customer = models.ForeignKey(
        "users.Customer",
        on_delete=models.CASCADE,
        related_name="rewards",
    )

    reward_type = models.CharField(
        max_length=20,
        choices=RewardType.choices,
    )

    points = models.PositiveIntegerField(default=0)

    value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
    )

    status = models.CharField(
        max_length=20,
        choices=RewardStatus.choices,
        default=RewardStatus.AVAILABLE,
    )

    expiry_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.reward_type} - {self.id}"