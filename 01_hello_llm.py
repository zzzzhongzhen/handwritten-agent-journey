"""
第一步:跑通你和大模型的第一次对话。

运行前:
1. 安装 uv(只需一次):
   curl -LsSf https://astral.sh/uv/install.sh | sh
2. 在本文件夹初始化项目并装 SDK:
   uv init
   uv add anthropic
3. 去 console.anthropic.com 申请 API key,然后设置环境变量:
   export ANTHROPIC_API_KEY="你的key"
4. 运行:
   uv run 01_hello_llm.py
"""

from anthropic import Anthropic

# SDK 会自动读取环境变量 ANTHROPIC_API_KEY
client = Anthropic()

# 最简单的一次请求:你问一句,模型答一句
response = client.messages.create(
    model="claude-opus-4-8",          # 模型 id
    max_tokens=1024,                   # 最多生成多少 token
    system="你是一个友好的编程导师,用简洁中文回答。",  # system prompt:定义模型的角色
    messages=[
        {"role": "user", "content": "用一句话解释什么是 Agent?"}
    ],
)

# 模型的回复在 response.content[0].text 里
print(response.content[0].text)

# 试试看 token 用量(理解成本和上下文长度)
print("\n--- 用量 ---")
print(f"输入 token: {response.usage.input_tokens}")
print(f"输出 token: {response.usage.output_tokens}")
