"""Direct test of DeepSeek API"""
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
model = os.getenv("OPENAI_MODEL", "deepseek-coder")

print("=== DeepSeek API Test ===")
print(f"API Key: {api_key[:10]}...{api_key[-5:] if api_key else 'None'}")
print(f"Base URL: {base_url}")
print(f"Model: {model}")
print()

if not api_key:
    print("ERROR: API key not found in .env")
    exit(1)

try:
    client = OpenAI(api_key=api_key, base_url=base_url)
    print("Testing API call...")
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Say hello"}],
        max_tokens=10
    )
    print("SUCCESS! API is working!")
    print(f"Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {str(e)}")
    if hasattr(e, 'response') and e.response:
        print(f"Status: {e.response.status_code}")
        print(f"Response: {e.response.text[:200]}")

