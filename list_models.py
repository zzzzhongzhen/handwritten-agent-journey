# 查一下:你的 Kimi 账号到底能用哪些模型
# 运行:uv run list_models.py
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("MOONSHOT_API_KEY"),
    base_url="https://api.moonshot.cn/v1",
)

print("你的账号可用的模型:")
for m in client.models.list().data:
    print(" -", m.id)
