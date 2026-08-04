# 多轮对话 + 流式输出(打字机效果)Kimi 版
# 运行:uv run 12_chat_stream_kimi.py
#
# 和 11 的唯一区别:回复不再"等全部想完一次性蹦出",
# 而是"一个字一个字实时流出来"(像网页版那样)。

import os
from openai import OpenAI
from dotenv import load_dotenv
import time

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("MOONSHOT_API_KEY"),
    base_url="https://api.moonshot.cn/v1",
)

messages = [
    {"role": "system", "content": "你是一个友好的助手,回答简洁。"},
]

print("💬 开始聊天(输入 quit 退出)\n")

while True:
    user_input = input("你: ")
    if user_input.lower() in ("quit", "exit", "退出"):
        print("再见!")
        break

    messages.append({"role": "user", "content": user_input})

    # ============================================================
    # 关键区别 1:加 stream=True,让 API 分块(chunk)返回,而不是一次性
    # ============================================================
    stream = client.chat.completions.create(
        model="kimi-k2.6",
        messages=messages,
        temperature=1,
        stream=True,          # ← 开启流式
    )

    # ============================================================
    # 关键区别 2:回复是"一块一块"来的,要遍历 stream 拼起来
    #   - 每块的新内容在 chunk.choices[0].delta.content(注意是 delta 不是 message!)
    #   - 有些块的 delta 是空的(None),要跳过
    #   - print(..., end="", flush=True):不换行、立即显示,才有打字机效果
    # ============================================================
    print("🤖 Kimi: ", end="", flush=True)
    reply = ""                                   # 用来把碎片拼成完整回复
    chunk_count = 0                              # 诊断:数一共收到几块
    for chunk in stream:
        delta = chunk.choices[0].delta.content   # 这一块的新文字
        if delta:                                # 空块跳过
            print(delta, end="", flush=True)     # 实时打印这一小块
            reply += delta                       # 同时攒进 reply
            chunk_count += 1
            time.sleep(0.1)
    print(f"\n  (诊断:本次回复共收到 {chunk_count} 块)\n")   # 块数 > 1 = 流式在工作

    # ============================================================
    # 关键点:存历史时,存的是"拼完整的 reply",不是某一块
    #   (流式只是"显示方式"变了,历史照样要存完整回复)
    # ============================================================
    messages.append({"role": "assistant", "content": reply})
