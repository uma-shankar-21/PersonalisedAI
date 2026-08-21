from apps.transactions.models import Transaction


def get_transactions(
    customer_id,
    start_date=None,
    end_date=None,
    transaction_date=None,
    category=None,
    merchant=None,
    transaction_type=None,
    status=None,
):
    transactions = (
        Transaction.objects
        .select_related("account")
        .filter(
            account__customer_id=customer_id
        )
    )

    if start_date:

        transactions = transactions.filter(
            transaction_date__date__gte=start_date
        )

    if end_date:

        transactions = transactions.filter(
            transaction_date__date__lte=end_date
        )

    if transaction_date:

        transactions = transactions.filter(
            transaction_date__date=transaction_date
        )

    if category:

        transactions = transactions.filter(
            category__iexact=category
        )

    if merchant:

        transactions = transactions.filter(
            merchant__icontains=merchant
        )

    if transaction_type:

        transactions = transactions.filter(
            transaction_type=transaction_type.upper()
        )

    if status:

        transactions = transactions.filter(
            status=status.upper()
        )

    transactions = (
        transactions
        .order_by("-transaction_date")
        .values(
            "transaction_date",
            "amount",
            "currency",
            "transaction_type",
            "category",
            "merchant",
            "status",
            "account__account_number",
            "account__account_type",
        )
    )

    return {
        "customer_id": str(customer_id),
        "count": transactions.count(),
        "transactions": list(transactions),
    }