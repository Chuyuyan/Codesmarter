import requests
import json

# ============
# 你的 DeepSeek API Key（直接写死测试用）
# ============
key = "sk-50e342a3694b489ba2a6d683ce4e8389"   # ← 宝贝把你的 key 粘贴到这里

print("当前 key 长度:", len(key))
print("key 前 8 位:", key[:8])

# ============
# 发起请求
# ============
url = "https://api.deepseek.com/chat/completions"

headers = {
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
}

data = {
    "model": "deepseek-chat",
    "messages": [
        {"role": "user", "content": "hello from test script"}
    ],
}

try:
    resp = requests.post(url, headers=headers, json=data, timeout=30)
    print("HTTP 状态:", resp.status_code)
    print("响应内容:")
    print(resp.text)
except Exception as e:
    print("请求出错：", repr(e))
