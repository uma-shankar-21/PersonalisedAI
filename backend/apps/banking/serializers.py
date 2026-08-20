from rest_framework import serializers

from apps.banking.models import BankAccount


class BankAccountBalanceSerializer(serializers.ModelSerializer):

    class Meta:
        model = BankAccount

        fields = [
            "account_number",
            "account_type",
            "balance",
            "currency",
            "status",
        ]