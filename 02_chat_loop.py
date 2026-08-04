"""
第二步:多轮对话(第 4 周的里程碑目标)。

核心认知:
  LLM 本身是【无状态】的 —— 它不记得你上一句说了什么。
  "记忆" 完全靠你把【整个对话历史】每次都重新发给它。
  这一点理解了,你就懂了 agent 的半壁江山。

运行:
  uv run 02_chat_loop.py
  输入 quit 退出。
"""

from anthropic import Anthropic

client = Anthropic()

# 这个 list 就是"对话历史"。每轮对话都往里追加,然后整个传给模型。
# 这就是 agent 的"记忆" —— 看清楚它有多朴素。
messages = []

print("和 Claude 聊天吧(输入 quit 退出)\n")

while True:
    user_input = input("你: ").strip()
    if user_input.lower() in ("quit", "exit", "q"):
        print("再见!")
        break
    if not user_input:
        continue

    # 1. 把用户这句话加进历史
    messages.append({"role": "user", "content": user_input})

    # 2. 把【完整历史】发给模型,用流式输出(回复一个字一个字蹦)
    print("Claude: ", end="", flush=True)
    full_reply = ""
    with client.messages.stream(
        model="claude-opus-4-8",
        max_tokens=1024,
        system="你是一个友好的编程导师,用简洁中文回答。",
        messages=messages,
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            full_reply += text
    print("\n")

    # 3. 把模型的回复也加进历史 —— 下一轮它才"记得"刚才说过的话
    messages.append({"role": "assistant", "content": full_reply})

    # 想看"记忆"长什么样,取消下面这行的注释:
    # print(f"[当前历史共 {len(messages)} 条消息]\n")
