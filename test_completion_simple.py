"""
Simple quick test for inline completion feature.
Run this to quickly verify completion is working.
"""
import requests
import sys

SERVER_URL = "http://127.0.0.1:5050"

def quick_test():
    """Quick test of completion endpoint."""
    print("Testing inline completion endpoint...\n")
    
    # Check backend
    try:
        health = requests.get(f"{SERVER_URL}/health", timeout=5)
        if health.status_code != 200:
            print("❌ Backend server is not responding")
            print("   Start it with: python -m backend.app")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        print("   Start server with: python -m backend.app")
        return False
    
    print("✅ Backend server is running\n")
    
    # Test completion
    file_content = """def process_order(order):
    # TODO: implement order processing
    """
    
    print("Sending completion request...")
    response = requests.post(
        f"{SERVER_URL}/completion",
        json={
            "file_path": "test.py",
            "file_content": file_content,
            "cursor_line": 2,
            "cursor_column": 35,  # After "// TODO: implement order processing"
            "num_completions": 1,
            "max_tokens": 200
        },
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"❌ Request failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False
    
    data = response.json()
    
    if not data.get("ok"):
        print(f"❌ Completion failed: {data.get('error', 'Unknown error')}")
        return False
    
    completion = data.get("primary_completion", "")
    
    if not completion:
        print("❌ No completion generated")
        return False
    
    print("✅ Completion generated successfully!")
    print(f"\nCompletion ({len(completion)} chars):")
    print("-" * 60)
    print(completion)
    print("-" * 60)
    
    return True

if __name__ == "__main__":
    success = quick_test()
    sys.exit(0 if success else 1)

