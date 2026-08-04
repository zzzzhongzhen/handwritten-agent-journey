# 🎉 你的代码第一次和大模型对话!(Kimi / 月之暗面版)
# 先装:uv add openai   (Kimi 兼容 OpenAI 接口,所以用 openai 这个库)
# 运行:uv run 10_hello_kimi.py
#
# 【运行前必做】设置 API key(二选一):
#   方式一(快速测试,当前终端有效):
#       export MOONSHOT_API_KEY="你的key"     然后在同一个终端 uv run
#   方式二(推荐,下周细讲):把 key 存进项目根目录的 .env 文件
#       文件内容一行:MOONSHOT_API_KEY=你的key
#       (然后 uv add python-dotenv,并解开下面 dotenv 相关的注释)

import os
from openai import OpenAI

# ---- 如果你用 .env 方式,解开下面两行注释 ----
# from dotenv import load_dotenv
# load_dotenv()

# ============================================================
# 1. 从环境变量读 API key(绝不写死在代码里!)
#    这是你第 2 周学的"环境变量"的实战:key 和代码分离,安全
# ============================================================
api_key = os.environ.get("MOONSHOT_API_KEY")
if not api_key:
    print("❌ 没找到 API key。先 export MOONSHOT_API_KEY=... 或配好 .env")
    raise SystemExit(1)      # 直接退出,别往下跑

# ============================================================
# 2. 创建客户端(client)
#    base_url 指向 Kimi 的地址 —— 这就是"换成别家 API"的关键:
#    以后想换 DeepSeek/Anthropic,主要就是改 base_url + key + 模型名
# ============================================================
client = OpenAI(
    api_key=api_key,
    base_url="https://api.moonshot.cn/v1",   # Kimi 的接口地址
)

# ============================================================
# 3. ⭐ messages 结构:大模型对话的核心格式
#    是一个"列表",每条是一个 dict,有 role 和 content
#    role 有三种:
#      - system:  设定模型的身份/行为(全局指令,最先给)
#      - user:    你说的话
#      - assistant: 模型说的话(多轮对话时用来带上历史)
# ============================================================
messages = [
    {"role": "system", "content": "你是一个友好的编程老师,擅长把复杂概念讲简单。"},
    {"role": "user", "content": "你能做什么"},
]

# ============================================================
# 4. 发起请求(和大模型对话)
# ============================================================
print("⏳ 正在请求 Kimi...\n")
response = client.chat.completions.create(
    model="kimi-k2.6",           # 你账号可用的通用模型(用 list_models.py 查出来的)
    messages=messages,
    temperature=1,               # kimi-k2.6 只允许 temperature=1(新模型锁死了这个参数)
)

# ============================================================
# 5. 取出模型的回复
#    回复藏在 response.choices[0].message.content 里(记住这个路径)
# ============================================================
reply = response.choices[0].message.content
print("🤖 Kimi 说:")
print(reply)

# ============================================================
# 6. 看看 token 消耗(计费和"上下文长度"都按 token 算)
#    token ≈ 文本的最小计费单位,中文大约 1 字 ≈ 1~2 token
# ============================================================
print("\n--- token 消耗 ---")
print(f"输入 token: {response.usage.prompt_tokens}")
print(f"输出 token: {response.usage.completion_tokens}")
print(f"总计:     {response.usage.total_tokens}")

# ============================================================
# 🎯 你来玩(改代码,体会效果)
# ============================================================
# TODO 1:改 system,让 Kimi 扮演别的角色(比如"你是一只高冷的猫"),
#         再看回复的语气变化。
# TODO 2:把 temperature 改成 0,再改成 1,同一个问题各跑两次,
#         观察 0 的回答是不是更稳定、1 的是不是更花。
# TODO 3:改 user 的问题,问点你真想问的。
