from apps.assistant.tools.account_tools import (
    get_account_balances,
)

from apps.assistant.tools.transaction_tools import (
    get_transactions,
)

from apps.assistant.tools.loan_tools import (
    get_customer_loans,
    get_loan_payment_history,
)


def get_customer_banking_data(
    customer_id,
    resources=None,
    resource=None,
    filters=None,
):

    # -----------------------------------------
    # NORMALIZE INPUT
    # -----------------------------------------

    if resources is None:
        resources = []

    # Support singular "resource" from LLM
    if resource:

        if isinstance(resource, list):

            resources.extend(resource)

        else:

            resources.append(resource)

    # If resources is accidentally sent as string
    if isinstance(resources, str):

        resources = [resources]

    # Remove duplicates
    resources = list(
        dict.fromkeys(resources)
    )

    # Default filters
    if filters is None:

        filters = {}

    result = {
        "customer_id": customer_id,
    }

    # -----------------------------------------
    # ACCOUNTS
    # -----------------------------------------

    if "accounts" in resources:

        result["accounts"] = (
            get_account_balances(
                customer_id=customer_id,
            )
        )

    # -----------------------------------------
    # TRANSACTIONS
    # -----------------------------------------

    if "transactions" in resources:

        transaction_filters = filters.get(
            "transactions",
            {},
        )

        result["transactions"] = (
            get_transactions(
                customer_id=customer_id,
                **transaction_filters,
            )
        )

    # -----------------------------------------
    # LOANS
    # -----------------------------------------

    if "loans" in resources:

        loan_filters = filters.get(
            "loans",
            {},
        )

        result["loans"] = (
            get_customer_loans(
                customer_id=customer_id,
                **loan_filters,
            )
        )

    # -----------------------------------------
    # LOAN PAYMENTS
    # -----------------------------------------

    if "loan_payments" in resources:

        payment_filters = filters.get(
            "loan_payments",
            {},
        )

        result["loan_payments"] = (
            get_loan_payment_history(
                customer_id=customer_id,
                **payment_filters,
            )
        )

    return result