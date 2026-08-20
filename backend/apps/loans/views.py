from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.loans.serializers import (
    LoanSummarySerializer,
    LoanPaymentSerializer,
)

from apps.loans.models import (
    Loan,
    LoanPayment,
)

class CustomerLoansAPIView(APIView):

    def post(self, request):

        customer_id = request.data.get(
            "customer_id"
        )

        if not customer_id:

            return Response(
                {
                    "error": "customer_id is required"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        loans = (
            Loan.objects
            .filter(
                customer_id=customer_id
            )
            .order_by(
                "-created_at"
            )
        )

        serializer = (
            LoanSummarySerializer(
                loans,
                many=True,
            )
        )

        return Response(
            {
                "count": loans.count(),
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

class LoanPaymentHistoryAPIView(APIView):

    def post(self, request):

        data = request.data

        loan_id = data.get(
            "loan_id"
        )

        if not loan_id:

            return Response(
                {
                    "error": "loan_id is required"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        payments = (
            LoanPayment.objects
            .select_related("loan")
            .filter(
                loan_id=loan_id
            )
        )

        start_date = data.get(
            "start_date"
        )

        end_date = data.get(
            "end_date"
        )

        if start_date:

            payments = payments.filter(
                payment_date__date__gte=start_date
            )

        if end_date:

            payments = payments.filter(
                payment_date__date__lte=end_date
            )

        payments = payments.order_by(
            "-payment_date"
        )

        serializer = (
            LoanPaymentSerializer(
                payments,
                many=True,
            )
        )

        return Response(
            {
                "loan_id": loan_id,
                "count": payments.count(),
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )