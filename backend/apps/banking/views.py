from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.banking.models import BankAccount
from apps.banking.serializers import (
    BankAccountBalanceSerializer,
)


class CustomerBankAccountsAPIView(APIView):

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

        accounts = (
            BankAccount.objects
            .filter(
                customer_id=customer_id
            )
            .order_by("account_type")
        )

        serializer = (
            BankAccountBalanceSerializer(
                accounts,
                many=True,
            )
        )

        return Response(
            {
                "count": accounts.count(),
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )