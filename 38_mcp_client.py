# 🔌 MCP 客户端 —— 连上 37 号 server(子进程),发现工具、跨进程调用
# 运行:uv run 38_mcp_client.py(它会自动把 37 号当子进程启动)
#
# 这才是 MCP 的精髓:server 跑在【另一个进程】,客户端通过【标准协议】发现并调用它的工具。
# 对比你手写的 TOOL_FUNCTIONS 字典(进程内查表)——这里是「跨进程 + 标准协议」。
#
# 注:这是异步代码(async/await)——MCP 走的是异步 IO。看不懂的地方先照着填,概念我讲。

import asyncio
from mcp import ClientSession, StdioServerParameters, stdio_client

# 启动参数:把 37 号 server 作为「子进程」跑起来(命令 = uv run 37_mcp_server.py)
server_params = StdioServerParameters(command="uv", args=["run", "37_mcp_server.py"])


async def mcp_run():
    # stdio_client 启动 server 子进程,给你两条管道(read 读 / write 写)
    async with stdio_client(server_params) as (read, write):
        # ClientSession 用这两条管道跟 server 对话
        async with ClientSession(read, write) as session:
            await session.initialize()          # 握手(MCP 协议第一步)

            # ── 该你写①:发现工具(MCP 核心动作,你手写版根本没有这步)──
            # 问 server:"你有哪些工具?" —— 工具不是写死在客户端,是运行时【问】出来的
            tools = await session.list_tools()                         # TODO:await session.list_tools()
            print("🔍 server 提供的工具:", [t.name for t in tools.tools])

            # ── 该你写②:跨进程调用一个工具 ──
            # 调 calculate 算 6*7(参数是个 dict:{"expression": "6*7"})
            result = await session.call_tool("calculate", {"expression": "6*7"})
            print("🧮 calculate(6*7) →", result.content[0].text)

            # 再调 get_weather 试试(这个给你写好,照上面的样子理解)
            result2 = await session.call_tool("get_weather", {"city": "深圳"})
            print("🌤️ get_weather(北京) →", result2.content[0].text)


asyncio.run(mcp_run())     # 启动异步主函数
