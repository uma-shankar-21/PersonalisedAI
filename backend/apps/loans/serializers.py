from django.utils import timezone

from rest_framework import serializers

from apps.loans.models import Loan,LoanPayment

class LoanPaymentSerializer(
    serializers.ModelSerializer
):

    class Meta:

        model = LoanPayment

        fields = [
            "payment_number",
            "amount",
            "payment_date",
        ]
        
class LoanSummarySerializer(
    serializers.ModelSerializer
):

    remaining_months = serializers.SerializerMethodField()

    class Meta:

        model = Loan

        fields = [
            "id",
            "loan_type",
            "principal_amount",
            "outstanding_amount",
            "interest_rate",
            "monthly_emi",
            "tenure_years",
            "remaining_months",
            "next_due_date",
            "status",
            "created_at",
        ]

    def get_remaining_months(
        self,
        obj,
    ):

        today = timezone.now().date()

        start_date = obj.created_at.date()

        elapsed_months = (
            (today.year - start_date.year)
            * 12
            + today.month
            - start_date.month
        )

        total_months = (
            obj.tenure_years * 12
        )

        remaining_months = (
            total_months
            - elapsed_months
        )

        return max(
            remaining_months,
            0,
        )