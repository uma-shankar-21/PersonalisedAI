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


TOOL_REGISTRY = {

    "get_account_balances": {
        "description": (
            "Get all savings and current bank accounts "
            "with their current balances and status."
        ),
        "parameters": {},
        "function": get_account_balances,
    },

    "get_transactions": {
        "description": (
            "Search customer transactions using optional "
            "filters such as date range, specific date, "
            "category, merchant, transaction type, "
            "and transaction status."
        ),
        "parameters": {
            "start_date": (
                "optional date in YYYY-MM-DD format"
            ),
            "end_date": (
                "optional date in YYYY-MM-DD format"
            ),
            "transaction_date": (
                "optional specific date in YYYY-MM-DD format"
            ),
            "category": (
                "optional transaction category such as "
                "FOOD, SHOPPING, TRAVEL, EMI"
            ),
            "merchant": (
                "optional merchant name"
            ),
            "transaction_type": (
                "optional CREDIT or DEBIT"
            ),
            "status": (
                "optional COMPLETED, FAILED, or PENDING"
            ),
        },
        "function": get_transactions,
    },

    "get_customer_loans": {
        "description": (
            "Get the customer's loans including loan type, "
            "principal amount, outstanding amount, monthly EMI, "
            "tenure, interest rate, status, and next due date."
        ),
        "parameters": {
            "status": (
                "optional loan status such as ACTIVE, "
                "CLOSED, ABOUT_TO_CLOSE"
            ),
        },
        "function": get_customer_loans,
    },

    "get_loan_payment_history": {
        "description": (
            "Get payment history for a specific customer loan. "
            "Optionally filter payments by date range."
        ),
        "parameters": {
            "loan_id": (
                "required loan UUID"
            ),
            "start_date": (
                "optional date in YYYY-MM-DD format"
            ),
            "end_date": (
                "optional date in YYYY-MM-DD format"
            ),
        },
        "function": get_loan_payment_history,
    },
}


def get_available_tools():
    """
    Return only tool metadata for the LLM.

    Function objects must not be sent to the LLM.
    """

    available_tools = {}

    for tool_name, tool_data in TOOL_REGISTRY.items():

        available_tools[tool_name] = {
            "description": tool_data[
                "description"
            ],
            "parameters": tool_data[
                "parameters"
            ],
        }

    return available_tools


def execute_tool(
    tool_name,
    payload,
):
    """
    Execute a registered banking tool.
    """

    if not tool_name:

        raise ValueError(
            "No tool was selected"
        )

    tool_data = TOOL_REGISTRY.get(
        tool_name
    )

    if not tool_data:

        raise ValueError(
            f"Unknown tool: {tool_name}"
        )

    tool_function = tool_data.get(
        "function"
    )

    return tool_function(
        **payload
    )