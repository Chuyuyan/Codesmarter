"""Diagnose DeepSeek API configuration"""
import os
from pathlib import Path

# Find .env file
env_path = Path('.env')
print(f".env file exists: {env_path.exists()}")
if env_path.exists():
    print(f".env file path: {env_path.absolute()}")
    print(f".env file size: {env_path.stat().st_size} bytes")
    print("\n.env file contents:")
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            if 'API_KEY' in line or 'BASE_URL' in line or 'MODEL' in line:
                # Mask API key for display
                if 'API_KEY' in line:
                    parts = line.split('=')
                    if len(parts) == 2:
                        key = parts[1].strip()
                        print(f"{parts[0]}=sk-...{key[-5:] if len(key) > 10 else 'SHORT'}")
                    else:
                        print(line.strip())
                else:
                    print(line.strip())
    
    # Now load it
    from dotenv import load_dotenv
    load_dotenv(env_path)
    
    print("\n=== Environment Variables (after loading) ===")
    api_key = os.getenv('OPENAI_API_KEY', '')
    base_url = os.getenv('OPENAI_BASE_URL', '')
    model = os.getenv('OPENAI_MODEL', '')
    
    print(f"OPENAI_API_KEY loaded: {bool(api_key)}")
    if api_key:
        print(f"OPENAI_API_KEY length: {len(api_key)}")
        print(f"OPENAI_API_KEY starts with: {api_key[:7]}")
        print(f"OPENAI_API_KEY format: {'✓ Valid (sk-...)' if api_key.startswith('sk-') else '✗ Invalid format'}")
    else:
        print("OPENAI_API_KEY: NOT LOADED")
    
    print(f"OPENAI_BASE_URL: {base_url}")
    print(f"OPENAI_MODEL: {model}")
    
    # Test backend config
    print("\n=== Backend Configuration ===")
    try:
        from backend.config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL, LLM_PROVIDER
        print(f"LLM_PROVIDER: {LLM_PROVIDER}")
        print(f"Backend OPENAI_API_KEY loaded: {bool(OPENAI_API_KEY)}")
        print(f"Backend OPENAI_BASE_URL: {OPENAI_BASE_URL}")
        print(f"Backend OPENAI_MODEL: {OPENAI_MODEL}")
        
        if OPENAI_API_KEY:
            print(f"Backend API Key starts with: {OPENAI_API_KEY[:7]}")
            print(f"Backend API Key length: {len(OPENAI_API_KEY)}")
            
            # Test client initialization
            print("\n=== Client Initialization Test ===")
            from backend.modules.llm_api import get_client
            try:
                client = get_client()
                print(f"Client type: {type(client)}")
                print("✓ Client initialized successfully")
                
                # Check client attributes
                if hasattr(client, 'base_url'):
                    print(f"Client base_url: {client.base_url}")
                elif hasattr(client, '_client') and hasattr(client._client, 'base_url'):
                    print(f"Client _client.base_url: {client._client.base_url}")
            except Exception as e:
                print(f"✗ Client initialization failed: {e}")
    except Exception as e:
        print(f"Error loading backend config: {e}")
        import traceback
        traceback.print_exc()

