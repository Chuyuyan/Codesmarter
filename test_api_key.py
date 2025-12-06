"""Test DeepSeek API key directly"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY", "")
base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
model = os.getenv("OPENAI_MODEL", "deepseek-coder")

print("=" * 60)
print("TESTING DEEPSEEK API KEY")
print("=" * 60)
print(f"API Key: {api_key[:10]}...{api_key[-5:] if len(api_key) > 15 else ''}")
print(f"Base URL: {base_url}")
print(f"Model: {model}")
print()

if not api_key:
    print("ERROR: API key not found in .env")
    sys.exit(1)

try:
    from openai import OpenAI
    
    client = OpenAI(api_key=api_key, base_url=base_url)
    
    print("Testing with model:", model)
    print("Sending test request...")
    
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Say hello in one word"}],
        max_tokens=5
    )
    
    print("\n" + "=" * 60)
    print("SUCCESS! API key is valid!")
    print("=" * 60)
    print(f"Response: {response.choices[0].message.content}")
    print(f"Model used: {response.model}")
    
except Exception as e:
    print("\n" + "=" * 60)
    print("FAILED!")
    print("=" * 60)
    print(f"Error: {type(e).__name__}")
    print(f"Message: {str(e)}")
    
    if "Authentication" in str(e) or "governor" in str(e).lower():
        print("\n" + "=" * 60)
        print("AUTHENTICATION ERROR - Possible Causes:")
        print("=" * 60)
        print("1. API key is INVALID or EXPIRED")
        print("2. API key doesn't have access to model:", model)
        print("3. API key quota/credits exhausted")
        print("4. API key format is wrong")
        print("\nSOLUTIONS:")
        print("1. Check your DeepSeek dashboard: https://platform.deepseek.com/")
        print("2. Generate a NEW API key")
        print("3. Verify the key is active and has credits")
        print("4. Try model 'deepseek-chat' instead of 'deepseek-coder'")
        
        # Try with alternative model
        print("\n" + "=" * 60)
        print("Trying alternative model: deepseek-chat")
        print("=" * 60)
        try:
            response2 = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": "Say hello"}],
                max_tokens=5
            )
            print("SUCCESS with deepseek-chat!")
            print(f"Response: {response2.choices[0].message.content}")
            print("\nSOLUTION: Change OPENAI_MODEL to 'deepseek-chat' in .env")
        except Exception as e2:
            print(f"Also failed with deepseek-chat: {str(e2)}")
            print("\nThe API key itself appears to be invalid.")
    
    sys.exit(1)

