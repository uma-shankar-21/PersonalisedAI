from apps.assistant.tools.banking_tools import (
    get_customer_banking_data,
)


TOOL_REGISTRY = {

    "get_customer_banking_data": {
        "description": (
            "Get banking information belonging ONLY to the current "
            "authenticated customer. This tool can retrieve account "
            "information, transactions, loans, and loan payment history. "
            "Use filters when the user's question contains specific "
            "requirements such as category, merchant, transaction type, "
            "status, date range, or loan status."
        ),
        "parameters": {
            "resources": {
                "description": (
                    "List of banking resources required to answer "
                    "the user's question."
                ),
                "allowed_values": [
                    "accounts",
                    "transactions",
                    "loans",
                    "loan_payments",
                ],
            },
            "filters": {
                "description": (
                    "Optional filters depending on the requested resource."
                ),
            },
        },
        "function": get_customer_banking_data,
    },
}


def get_available_tools():

    return TOOL_REGISTRY


def execute_tool(
    tool_name,
    payload,
):

    tool = TOOL_REGISTRY.get(
        tool_name
    )

    if not tool:

        raise ValueError(
            f"Unknown tool: {tool_name}"
        )

    tool_function = tool[
        "function"
    ]

    return tool_function(
        **payload
    )