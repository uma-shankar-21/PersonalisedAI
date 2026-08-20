from rest_framework import serializers

from apps.transactions.models import Transaction


class TransactionSerializer(serializers.ModelSerializer):

    account_number = serializers.CharField(
        source="account.account_number",
        read_only=True,
    )

    account_type = serializers.CharField(
        source="account.account_type",
        read_only=True,
    )

    class Meta:

        model = Transaction

        fields = [
            "id",
            "account_number",
            "account_type",
            "transaction_type",
            "amount",
            "currency",
            "description",
            "merchant",
            "transaction_date",
            "category",
            "status",
        ]