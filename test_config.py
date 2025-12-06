"""Test configuration loading"""
import os
from dotenv import load_dotenv

load_dotenv()

print("=== Environment Variables ===")
print(f"OPENAI_API_KEY exists: {bool(os.getenv('OPENAI_API_KEY'))}")
if os.getenv('OPENAI_API_KEY'):
    key = os.getenv('OPENAI_API_KEY')
    print(f"OPENAI_API_KEY length: {len(key)}")
    print(f"OPENAI_API_KEY prefix: {key[:7]}...")
print(f"OPENAI_BASE_URL: {os.getenv('OPENAI_BASE_URL')}")
print(f"OPENAI_MODEL: {os.getenv('OPENAI_MODEL')}")
print(f"LLM_PROVIDER: {os.getenv('LLM_PROVIDER', 'deepseek (default)')}")

print("\n=== Backend Configuration ===")
from backend.config import *
from backend.modules.llm_api import get_client

print(f"LLM_PROVIDER: {LLM_PROVIDER}")
print(f"DEEPSEEK_API_KEY set: {bool(DEEPSEEK_API_KEY)}")
print(f"OPENAI_API_KEY set: {bool(OPENAI_API_KEY)}")
print(f"OPENAI_BASE_URL: {OPENAI_BASE_URL}")
print(f"OPENAI_MODEL: {OPENAI_MODEL}")
print(f"LLM_MODEL: {LLM_MODEL}")

print("\n=== Client Configuration ===")
try:
    client = get_client()
    print(f"Client type: {type(client)}")
    # Check client attributes
    if hasattr(client, 'base_url'):
        print(f"Client base_url: {client.base_url}")
    if hasattr(client, '_client') and hasattr(client._client, 'base_url'):
        print(f"Client _client.base_url: {client._client.base_url}")
except Exception as e:
    print(f"Error creating client: {e}")

