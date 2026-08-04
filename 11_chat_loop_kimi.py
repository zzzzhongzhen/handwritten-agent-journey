# 多轮对话:能连续聊天的命令行工具(Kimi 版)
# 先装:uv add python-dotenv
# 需要项目根目录有 .env 文件,里面:MOONSHOT_API_KEY=你的key
# 运行:uv run 11_chat_loop_kimi.py
#
# 【本课核心】大模型是"无状态"的——它不记得你上一句说了啥!
#   对话历史要靠你自己存着(messages 列表),每次把完整历史传回去。

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()      # 自动读取 .env 文件里的 key,贴到"环境黑板"上

client = OpenAI(
    api_key=os.environ.get("MOONSHOT_API_KEY"),
    base_url="https://api.moonshot.cn/v1",
)

# messages 就是"对话历史",一开始只有 system 设定
messages = [
    {"role": "system", "content": "你是一个友好的助手,回答简洁。"},
]

print("💬 开始聊天(输入 quit 退出)\n")

while True:
    # 1. 拿用户输入
    user_input = input("你: ")
    if user_input.lower() in ("quit", "exit", "退出"):
        print("再见!")
        break

    # 2. 把用户这句话加进历史
    messages.append({"role": "user", "content": user_input})

    # 调试:打印出这次要发给模型的完整历史,亲眼看里面有啥
    print("  ┌── 本次发给模型的历史 ──")
    for m in messages:
        print(f"  │ [{m['role']}] {m['content'][:25]}")
    print("  └────────────────────")

    # 3. 带着"完整历史"去请求(注意:传的是整个 messages,不是单句)
    response = client.chat.completions.create(
        model="kimi-k2.6",
        messages=messages,
        temperature=1,
    )
    reply = response.choices[0].message.content

    # 4. 打印回复
    print(f"🤖 Kimi: {reply}\n")

    # ============================================================
    # 🎯 TODO(本课关键一行):把 Kimi 的回复也加回历史!
    #    不加这行,下一轮请求时历史里就没有它刚说的话,
    #    模型就会"失忆"——记不住上下文。
    # 提示:messages.append({"role": "assistant", "content": reply})
    # ============================================================
    # 先别写这行!按下面的实验步骤来。
    messages.append({"role": "assistant", "content": reply})