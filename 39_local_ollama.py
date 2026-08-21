# 🖥️ 本地模型 hello —— 同一套 openai 代码,只换 3 个地方,就从 Kimi 切到本地
# 运行:uv run 39_local_ollama.py(先确保 Ollama 服务在跑)
#
# 关键体验:Ollama 开的是「OpenAI 兼容」的服务,所以你熟的 openai 库直接能用——
#   和调 Kimi 相比,只有 base_url / api_key / model 三处不同,其余一模一样。

from openai import OpenAI

# ── 关键:把 client 指向本地 Ollama(而不是 Kimi 的云地址)──
client = OpenAI(
    base_url="http://localhost:11434/v1",      # TODO①:本地 Ollama 的 OpenAI 兼容地址 → "http://localhost:11434/v1"
    api_key="ollama",       # TODO②:本地不校验密钥,随便填个非空字符串,比如 "ollama"
)

# TODO③:你的本地模型名(就是 ollama list 里 NAME 那一列,一字不差)
MODEL = "modelscope.cn/Qwen/Qwen2.5-7B-Instruct-GGUF:latest"

resp = client.chat.completions.create(
    model=MODEL,
    messages=[{"role": "system", "content": "你是运行在用户 Mac 上的本地模型"}, {"role": "user", "content": "claude code是什么"}],
)
print("🤖 本地模型说:", resp.choices[0].message.content)
