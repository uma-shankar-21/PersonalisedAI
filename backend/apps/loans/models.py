import uuid

from django.db import models


class Loan(models.Model):

    class LoanType(models.TextChoices):
        CAR = "CAR", "Car"
        BIKE = "BIKE", "Bike"
        HOME = "HOME", "Home"
        PERSONAL = "PERSONAL", "Personal"
        BUSINESS = "BUSINESS", "Business"
        GOLD = "GOLD", "Gold"

    class LoanStatus(models.TextChoices):
        OPEN = "OPEN", "Open"
        PENDING = "PENDING", "Pending"
        ABOUT_TO_CLOSE = "ABOUT_TO_CLOSE", "About to Close"

    class Meta:
        db_table = "loans"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    customer = models.ForeignKey(
        "users.Customer",
        on_delete=models.CASCADE,
        related_name="loans",
    )

    loan_type = models.CharField(
        max_length=20,
        choices=LoanType.choices,
    )

    principal_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
    )

    outstanding_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
    )

    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    monthly_emi = models.DecimalField(
        max_digits=15,
        decimal_places=2,
    )

    tenure_years = models.PositiveIntegerField()
    
    next_due_date = models.DateField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=LoanStatus.choices,
        default=LoanStatus.OPEN,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.loan_type} - {self.id}"


class LoanPayment(models.Model):

    class Meta:
        db_table = "loan_payments"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    loan = models.ForeignKey(
        Loan,
        on_delete=models.CASCADE,
        related_name="payments",
    )

    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
    )

    payment_date = models.DateTimeField()

    payment_number = models.PositiveIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.payment_number} - {self.amount}"