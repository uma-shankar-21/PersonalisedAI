from django.db.models import Q

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.transactions.models import Transaction
from apps.transactions.serializers import TransactionSerializer


class TransactionSearchAPIView(APIView):

    def post(self, request):

        data = request.data

        customer_id = data.get("customer_id")

        if not customer_id:

            return Response(
                {
                    "error": "customer_id is required"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        transactions = (
            Transaction.objects
            .select_related(
                "account",
                "account__customer",
            )
            .filter(
                account__customer_id=customer_id
            )
        )

        # -------------------------------------------------
        # DATE RANGE
        # -------------------------------------------------

        start_date = data.get("start_date")
        end_date = data.get("end_date")

        if start_date:

            transactions = transactions.filter(
                transaction_date__date__gte=start_date
            )

        if end_date:

            transactions = transactions.filter(
                transaction_date__date__lte=end_date
            )

        # -------------------------------------------------
        # SINGLE DATE
        # -------------------------------------------------

        transaction_date = data.get(
            "transaction_date"
        )

        if transaction_date:

            transactions = transactions.filter(
                transaction_date__date=transaction_date
            )

        # -------------------------------------------------
        # CATEGORY
        # -------------------------------------------------

        category = data.get("category")

        if category:

            transactions = transactions.filter(
                category__iexact=category
            )

        # -------------------------------------------------
        # MERCHANT
        # -------------------------------------------------

        merchant = data.get("merchant")

        if merchant:

            transactions = transactions.filter(
                merchant__icontains=merchant
            )

        # -------------------------------------------------
        # TRANSACTION TYPE
        # CREDIT / DEBIT
        # -------------------------------------------------

        transaction_type = data.get(
            "transaction_type"
        )

        if transaction_type:

            transactions = transactions.filter(
                transaction_type=transaction_type.upper()
            )

        # -------------------------------------------------
        # STATUS
        # -------------------------------------------------

        transaction_status = data.get("status")

        if transaction_status:

            transactions = transactions.filter(
                status=transaction_status.upper()
            )

        transactions = transactions.order_by(
            "-transaction_date"
        )

        serializer = TransactionSerializer(
            transactions,
            many=True,
        )

        return Response(
            {
                "count": transactions.count(),
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )