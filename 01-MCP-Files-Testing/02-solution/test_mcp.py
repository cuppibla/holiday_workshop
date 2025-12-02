import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run():
    # Define server parameters
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"],
    )

    # Connect to the server
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print(f"Connected to server with tools: {[t.name for t in tools.tools]}")

            # Call the "add" tool
            result_add = await session.call_tool("add", arguments={"a": 5, "b": 3})
            print(f"5 + 3 = {result_add.content[0].text}")

            # Call the "multiply" tool
            result_mul = await session.call_tool("multiply", arguments={"a": 4, "b": 6})
            print(f"4 * 6 = {result_mul.content[0].text}")

if __name__ == "__main__":
    asyncio.run(run())
