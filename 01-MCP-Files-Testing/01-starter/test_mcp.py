import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run():
    # TODO: Define server parameters to run "python mcp_server.py"
    # server_params = StdioServerParameters(
    #     command="python",
    #     args=["mcp_server.py"],
    # )

    # TODO: Connect to the server using stdio_client
    # async with stdio_client(server_params) as (read, write):
    #     async with ClientSession(read, write) as session:
    #         # TODO: Initialize the session
    #         # await session.initialize()

    #         # TODO: List available tools
    #         # tools = await session.list_tools()
    #         # print(tools)

    #         # TODO: Call the "add" tool with arguments {"a": 5, "b": 3}
    #         # result = await session.call_tool("add", arguments={"a": 5, "b": 3})
    #         # print(f"5 + 3 = {result.content[0].text}")
    pass

if __name__ == "__main__":
    asyncio.run(run())
