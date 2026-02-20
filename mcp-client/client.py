"""
Minimal MCP (Model Context Protocol) client that:
- launches an MCP server over stdio (Python or Node)
- initializes an MCP session and lists available tools
- sends user prompts to Anthropic Claude and forwards any tool calls to the MCP server

Environment:
- expects Anthropic credentials in the environment (commonly via `ANTHROPIC_API_KEY`)
- `python-dotenv` is used to optionally load variables from a local `.env` file
"""

import asyncio
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables from a local `.env` file (if present).
# This is convenient for local development; production typically uses real env vars.
load_dotenv()

class MCPClient:
    """Holds long-lived client state (MCP session + Anthropic client) and manages cleanup."""

    def __init__(self):
        # MCP session gets created after connecting to the server.
        self.session: Optional[ClientSession] = None

        # AsyncExitStack makes it easy to close multiple async context managers in one place.
        self.exit_stack = AsyncExitStack()

        # Anthropic SDK client (reads credentials from environment).
        self.anthropic = Anthropic()

# NOTE:
# The async callables below are written with a `self` parameter, but they are currently
# module-level functions (not methods on `MCPClient`). If you intend to call them as
# `client.connect_to_server(...)`, etc., move/indent them inside `MCPClient` (or bind
# them onto the instance).

# --- Server connection management ---
async def connect_to_server(self, server_script_path: str):
    """Connect to an MCP server

    Args:
        server_script_path: Path to the server script (.py or .js)
    """
    # Decide how to launch the server based on the script extension.
    is_python = server_script_path.endswith('.py')
    is_js = server_script_path.endswith('.js')
    if not (is_python or is_js):
        raise ValueError("Server script must be a .py or .js file")

    command = "python" if is_python else "node"

    # Configure the MCP stdio transport (the server runs as a subprocess).
    server_params = StdioServerParameters(
        command=command,
        args=[server_script_path],
        env=None
    )

    # Create the stdio transport and MCP session, and register both with the ExitStack
    # so `cleanup()` can close them reliably.
    stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
    self.stdio, self.write = stdio_transport
    self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

    # Perform the MCP initialization handshake.
    await self.session.initialize()

    # List available tools
    response = await self.session.list_tools()
    tools = response.tools
    print("\nConnected to server with tools:", [tool.name for tool in tools])

# --- Query processing ---
async def process_query(self, query: str) -> str:
    """Process a user query with Claude, executing any MCP tool calls as needed."""
    # Claude "messages" format: a list of role/content turns.
    messages = [
        {
            "role": "user",
            "content": query
        }
    ]

    # Expose MCP tools to Claude in the schema the Anthropic SDK expects.
    response = await self.session.list_tools()
    available_tools = [{
        "name": tool.name,
        "description": tool.description,
        "input_schema": tool.inputSchema
    } for tool in response.tools]

    # Initial Claude API call
    response = self.anthropic.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=messages,
        tools=available_tools
    )

    # Accumulate a readable transcript of what happened.
    final_text = []

    # Keep track of the "assistant" content we send back to Claude when tool calls occur.
    assistant_message_content = []
    for content in response.content:
        if content.type == 'text':
            final_text.append(content.text)
            assistant_message_content.append(content)
        elif content.type == 'tool_use':
            # Claude requested a tool call; forward it to the MCP server.
            tool_name = content.name
            tool_args = content.input

            # Execute tool call
            result = await self.session.call_tool(tool_name, tool_args)
            final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

            # Append the tool-use message, then a tool-result message, so Claude can continue.
            assistant_message_content.append(content)
            messages.append({
                "role": "assistant",
                "content": assistant_message_content
            })
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": content.id,
                        "content": result.content
                    }
                ]
            })

            # Get next response from Claude
            response = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=messages,
                tools=available_tools
            )

            # This example assumes the follow-up contains at least one text block.
            final_text.append(response.content[0].text)

    return "\n".join(final_text)

# --- Interactive chat interface ---
async def chat_loop(self):
    """Run an interactive chat loop"""
    print("\nMCP Client Started!")
    print("Type your queries or 'quit' to exit.")

    while True:
        try:
            query = input("\nQuery: ").strip()

            if query.lower() == 'quit':
                break

            # Process query and print the assistant's response.
            response = await self.process_query(query)
            print("\n" + response)

        except Exception as e:
            print(f"\nError: {str(e)}")

async def cleanup(self):
    """Clean up resources (stdio transport, session, etc.)."""
    await self.exit_stack.aclose()

# --- Main entry point ---
async def main():
    # Basic CLI argument parsing: the server script to launch.
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)

    client = MCPClient()
    try:
        # Connect to the MCP server and then start the REPL.
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        # Always attempt cleanup, even if the chat loop fails.
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())
