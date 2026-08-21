import json


def build_tool_selection_prompt(
    user_message,
    customer_id,
    tools,
):

    tool_descriptions = []

    for tool in tools:

        tool_descriptions.append(
            {
                "name": tool["name"],
                "description": (
                    tool["description"]
                ),
            }
        )

    return f"""
You are a banking AI assistant.

Your job is to determine which tool is required
to answer the user's question.

CUSTOMER ID:
{customer_id}

AVAILABLE TOOLS:

{json.dumps(tool_descriptions, indent=2)}

USER QUESTION:

{user_message}

Return ONLY valid JSON.

Use this format:

{{
    "tool_name": "tool name",
    "arguments": {{
    }}
}}

RULES:

1. Use only tools from AVAILABLE TOOLS.
2. Never invent a tool name.
3. Always include the customer_id argument.
4. Extract dates, categories, merchants, transaction
   types, statuses, or loan IDs when required.
5. Return only JSON.
6. Do not include markdown.
"""