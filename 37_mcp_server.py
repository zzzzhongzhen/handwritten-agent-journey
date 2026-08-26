# 🔌 MCP Server —— 把工具从 agent 里拆出去,变成独立的标准服务
# 这是"服务端":它只负责暴露工具,自己不会主动干活。
# 怎么测:别直接 uv run(它会挂着等客户端);下一步我们写个客户端(38)来连它。
#
# 关键理解:@server.tool() 把一个普通函数「注册成 MCP 工具」——
#   一旦注册,任何 MCP 客户端(Claude Desktop / Cursor / 你的 agent)都能发现并调用它。
#   工具从"焊在某个 agent 里的函数"变成了"谁都能连的标准服务"。

import httpx
from mcp.server import MCPServer

# 给这个"工具服务"起个名字(客户端连上来会看到)
server = MCPServer("weather-calc-tools")

CITIES = {"北京": (39.90, 116.41), "上海": (31.23, 121.47), "深圳": (22.54, 114.06)}


# ── 该你写①:把下面两个函数「暴露」成 MCP 工具 ──
# 提示:在函数上面加装饰器 @server.tool()
#   docstring 依旧是"给模型/客户端看的说明"(MCP 会把它作为工具描述广播出去)
@server.tool()
def get_weather(city: str) -> str:
    """查询某个城市的当前温度(摄氏度)。要知道天气/温度时用。"""
    if city not in CITIES:
        return f"暂不支持城市:{city}"
    lat, lon = CITIES[city]
    r = httpx.get("https://api.open-meteo.com/v1/forecast",
                  params={"latitude": lat, "longitude": lon, "current_weather": True}, timeout=10)
    return f"{city}当前温度为:{r.json()['current_weather']['temperature']}°C"


@server.tool()
def calculate(expression: str) -> str:
    """计算数学表达式并返回精确结果。要算数时用。"""
    return str(eval(expression))


if __name__ == "__main__":
    # ── 该你写②:选一种传输方式启动 ──
    # 提示:本地把 server 当子进程跑、用标准输入输出通信 → "stdio"
    #      (另两种是 "sse" / "streamable-http",那是"作为网络服务"跑,远程多客户端用)
    server.run(transport="stdio")
