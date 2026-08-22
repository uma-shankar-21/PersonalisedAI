import json

from apps.assistant.llm.ollama_client import (
    generate_json,
    generate_response,
)

from apps.assistant.mcp.tools import (
    execute_tool,
    get_available_tools,
)

from apps.assistant.domain.relevance import (
    classify_query,
)

DOMAIN_FALLBACK = (
    "👋 Please ask a question related to your own banking "
    "information or this bank's products and services."
)

OTHER_PERSON_FALLBACK = (
    "🔒 I can only help with your own banking information."
)

UNAUTHORIZED_FALLBACK = (
    "⚠️ I can't help with unauthorized access, theft, or "
    "exploiting banking systems. I can help with legitimate "
    "questions about your account, transactions, and loans."
)


class ChatService:

    def chat(
        self,
        customer_id,
        message,
    ):

        # =============================================
        # STEP 1: DOMAIN / RELEVANCE CLASSIFICATION
        # =============================================

        classification = classify_query(
            message
        )

        category = classification.get(
            "category"
        )

        # ---------------------------------------------
        # OTHER PERSON'S PRIVATE BANKING DATA
        # ---------------------------------------------

        if category == "OTHER_PERSON_DATA":

            return {
                "message": OTHER_PERSON_FALLBACK,
                "tool_used": None,
                "tool_result": None,
            }

        # ---------------------------------------------
        # UNAUTHORIZED / MALICIOUS REQUEST
        # ---------------------------------------------

        if category == "UNAUTHORIZED_REQUEST":

            return {
                "message": UNAUTHORIZED_FALLBACK,
                "tool_used": None,
                "tool_result": None,
            }

        # ---------------------------------------------
        # CLEARLY OUT OF DOMAIN
        # ---------------------------------------------

        if category == "OUT_OF_DOMAIN":

            return {
                "message": DOMAIN_FALLBACK,
                "tool_used": None,
                "tool_result": None,
            }

        # =============================================
        # STEP 2: EXISTING LLM TOOL ROUTING
        #
        # PERSONAL_BANKING and AMBIGUOUS queries
        # are allowed to continue.
        # =============================================

        tool_decision = self.get_tool_decision(
            message=message,
        )

        tools = tool_decision.get(
            "tools",
            [],
        )

        # ---------------------------------------------
        # NO TOOL SELECTED
        # ---------------------------------------------

        if not tools:

            return {
                "message": (
                    "👋 I couldn't find a supported banking action "
                    "for that question. You can ask me about your "
                    "accounts, balances, transactions, loans, or "
                    "loan payments."
                ),
                "tool_used": None,
                "tool_result": None,
            }

        # =============================================
        # STEP 3: EXECUTE VALID TOOLS
        # =============================================

        tool_results = []

        available_tools = get_available_tools()

        for tool in tools:

            tool_name = tool.get(
                "tool"
            )

            payload = tool.get(
                "payload",
                {}
            )

            # -----------------------------------------
            # SECURITY:
            # Never trust customer_id from the LLM
            # -----------------------------------------

            payload["customer_id"] = customer_id

            # -----------------------------------------
            # Skip hallucinated tools
            # -----------------------------------------

            if tool_name not in available_tools:

                continue

            result = execute_tool(
                tool_name=tool_name,
                payload=payload,
            )

            tool_results.append(
                {
                    "tool": tool_name,
                    "result": result,
                }
            )

        # =============================================
        # STEP 4: NO VALID TOOL EXECUTED
        # =============================================

        if not tool_results:

            return {
                "message": DOMAIN_FALLBACK,
                "tool_used": None,
                "tool_result": None,
            }

        # =============================================
        # STEP 5: FINAL RESPONSE
        # =============================================

        final_response = self.generate_final_response(
            message=message,
            tool_results=tool_results,
        )

        # =============================================
        # STEP 6: RETURN
        # =============================================

        return {
            "message": final_response,
            "tool_used": [
                item["tool"]
                for item in tool_results
            ],
            "tool_result": tool_results,
        }

    # =================================================
    # TOOL DECISION
    # =================================================

    def get_tool_decision(
        self,
        message,
    ):

        tools_description = self.get_tools_description()

        prompt = f"""
You are a banking AI assistant.

Your ONLY job is to decide which available banking tools
are required to answer the user's question.

AVAILABLE TOOL:

get_customer_banking_data

Use this tool when the user's question requires information
about the user's own banking data.

AVAILABLE RESOURCES:

- accounts
- transactions
- loans
- loan_payments

RULES:

1. Select tools ONLY when the user's question can be answered
using the available banking tools.

2. If the question is unrelated to the user's banking data
or the bank's supported information, return an empty tools list.

3. Never answer the user's question.

4. Never use general world knowledge.

5. Do not invent tools.

6. A question may require multiple tools.

7. Extract relevant parameters from the user message.

8. Do NOT include customer_id.
It will be injected by the backend.

Return ONLY valid JSON in this exact format:

{{
    "tools": [
        {{
            "tool": "tool_name",
            "payload": {{
            }}
        }}
    ]
}}

If no available tool is appropriate:

{{
    "tools": []
}}

USER QUESTION:

{message}
"""

        decision = generate_json(
            prompt=prompt,
        )

        if not isinstance(
            decision,
            dict,
        ):

            return {
                "tools": [],
            }

        tools = decision.get(
            "tools",
            [],
        )

        if not isinstance(
            tools,
            list,
        ):

            return {
                "tools": [],
            }

        return {
            "tools": tools,
        }

    # =================================================
    # FINAL RESPONSE
    # =================================================

    def generate_final_response(
        self,
        message,
        tool_results,
    ):

        tool_data = json.dumps(
            tool_results,
            default=str,
            indent=2,
        )

        prompt = f"""
You are a banking AI assistant.

Answer the user's question using ONLY the banking data
provided below.

USER QUESTION:

{message}

BANKING TOOL RESULTS:

{tool_data}

STRICT RULES:

1. Use ONLY the provided tool results.

2. Do NOT use outside knowledge.

3. Do NOT invent information.

4. If the required information is not present in the tool
results, clearly say that the information is not available.

5. Be concise and helpful.

6. Do not mention internal tools, MCP, APIs, payloads,
or implementation details.

7. If the user's question is incomplete or additional
information would help answer a related banking question,
ask ONE short and relevant follow-up question.

8. Only ask a follow-up when it is genuinely useful.
Do not ask unnecessary questions after every response.

9. The follow-up question must be related only to:
- the user's accounts
- transactions
- loans
- loan payments
- supported bank products or services

10. Never ask about unrelated topics or request sensitive
information such as passwords, PINs, OTPs, or credentials.

Now answer the user.
"""

        return generate_response(
            prompt=prompt,
            temperature=0.2,
        )

    # =================================================
    # TOOL DESCRIPTION
    # =================================================

    def get_tools_description(
        self,
    ):

        available_tools = get_available_tools()

        descriptions = []

        for tool_name, tool_data in (
            available_tools.items()
        ):

            descriptions.append(
                f"""
TOOL NAME:
{tool_name}

DESCRIPTION:
{tool_data["description"]}

PARAMETERS:
{json.dumps(
    tool_data["parameters"],
    indent=2,
)}
"""
            )

        return "\n".join(
            descriptions
        )