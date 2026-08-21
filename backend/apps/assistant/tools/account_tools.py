from apps.banking.models import BankAccount


def get_account_balances(customer_id):
    accounts = (
        BankAccount.objects
        .filter(
            customer_id=customer_id,
        )
        .values(
            "account_number",
            "account_type",
            "balance",
            "status",
        )
        .order_by("account_type")
    )

    return {
        "customer_id": str(customer_id),
        "accounts": list(accounts),
    }