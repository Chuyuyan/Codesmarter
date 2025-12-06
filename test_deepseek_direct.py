"""Direct test of DeepSeek API with current credentials"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY", "")
base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
model = os.getenv("OPENAI_MODEL", "deepseek-coder")

print("=" * 60)
print("DEEPSEEK API DIRECT TEST")
print("=" * 60)
print(f"API Key: {api_key[:10]}...{api_key[-5:] if len(api_key) > 15 else 'SHORT'}")
print(f"API Key length: {len(api_key)}")
print(f"Base URL: {base_url}")
print(f"Model: {model}")
print()

if not api_key:
    print("ERROR: OPENAI_API_KEY not found in .env file")
    sys.exit(1)

if not api_key.startswith("sk-"):
    print(f"WARNING: API key format might be incorrect (expected 'sk-...', got '{api_key[:5]}...')")

try:
    from openai import OpenAI
    
    print("Initializing OpenAI client...")
    client = OpenAI(api_key=api_key, base_url=base_url)
    
    print("Sending test request to DeepSeek API...")
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Say hello"}],
        max_tokens=10
    )
    
    print("\n" + "=" * 60)
    print("SUCCESS! DeepSeek API is working!")
    print("=" * 60)
    print(f"Response: {response.choices[0].message.content}")
    print(f"Model used: {response.model}")
    
except ImportError:
    print("ERROR: openai package not installed")
    print("Install it with: pip install openai")
    sys.exit(1)
except Exception as e:
    print("\n" + "=" * 60)
    print("ERROR: DeepSeek API test failed")
    print("=" * 60)
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {str(e)}")
    
    if "Authentication" in str(e) or "governor" in str(e).lower():
        print("\nPossible causes:")
        print("1. API key is invalid or expired")
        print("2. API key format is incorrect")
        print("3. API key doesn't have access to DeepSeek API")
        print("4. Check your DeepSeek dashboard: https://platform.deepseek.com/")
        print("\nTo fix:")
        print("1. Get a valid API key from https://platform.deepseek.com/")
        print("2. Update .env file with: OPENAI_API_KEY=sk-your-key-here")
        print("3. Make sure the key starts with 'sk-'")
    
    if hasattr(e, 'response') and e.response:
        print(f"\nHTTP Status: {e.response.status_code}")
        try:
            print(f"Response: {e.response.text[:200]}")
        except:
            pass
    
    sys.exit(1)

