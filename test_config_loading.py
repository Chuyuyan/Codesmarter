"""Test if backend config loads the API key correctly"""
from dotenv import load_dotenv
from backend.config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL, LLM_PROVIDER
from backend.modules.llm_api import get_client

print("=" * 60)
print("BACKEND CONFIGURATION TEST")
print("=" * 60)

print(f"\nLLM_PROVIDER: {LLM_PROVIDER}")
print(f"OPENAI_API_KEY loaded: {bool(OPENAI_API_KEY)}")
if OPENAI_API_KEY:
    print(f"OPENAI_API_KEY: {OPENAI_API_KEY[:10]}...{OPENAI_API_KEY[-5:]}")
else:
    print("OPENAI_API_KEY: NOT LOADED!")
print(f"OPENAI_BASE_URL: {OPENAI_BASE_URL}")
print(f"OPENAI_MODEL: {OPENAI_MODEL}")

print("\n" + "=" * 60)
print("TESTING CLIENT INITIALIZATION")
print("=" * 60)

try:
    client = get_client()
    print(f"✓ Client initialized: {type(client)}")
    
    # Test API call
    print("\nTesting API call...")
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": "Say hello"}],
        max_tokens=5
    )
    print("✓ SUCCESS! API is working!")
    print(f"Response: {response.choices[0].message.content}")
    
except Exception as e:
    print(f"✗ ERROR: {type(e).__name__}")
    print(f"Message: {str(e)}")
    if "Authentication" in str(e):
        print("\nAuthentication error - check your API key!")

