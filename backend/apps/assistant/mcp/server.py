from apps.assistant.mcp.tools import (
    get_available_tools,
    execute_tool,
)


class MCPServer:

    def list_tools(self):

        tools = []

        for name, tool in (
            get_available_tools().items()
        ):

            tools.append(
                {
                    "name": name,
                    "description": (
                        tool["description"]
                    ),
                }
            )

        return tools

    def call_tool(
        self,
        tool_name,
        arguments,
    ):

        return execute_tool(
            tool_name=tool_name,
            arguments=arguments,
        )


mcp_server = MCPServer()