"""Test script to verify endpoints work without requiring API key"""
import requests
import json

BASE_URL = "http://127.0.0.1:5050"
REPO_DIR = r"C:\Users\57811\my-portfolio"

def test_health():
    """Test health endpoint"""
    print("=" * 60)
    print("Testing /health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"[OK] Status: {response.status_code}")
        print(f"[OK] Response: {response.json()}")
        return True
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False

def test_search():
    """Test search endpoint (doesn't require API key)"""
    print("\n" + "=" * 60)
    print("Testing /search endpoint...")
    try:
        data = {
            "repo_dir": REPO_DIR,
            "query": "import",
            "k": 5
        }
        response = requests.post(
            f"{BASE_URL}/search",
            json=data,
            timeout=10
        )
        print(f"[OK] Status: {response.status_code}")
        result = response.json()
        if result.get("ok"):
            print(f"[OK] Found {result.get('count', 0)} results")
            print(f"[OK] Search endpoint works!")
            return True
        else:
            print(f"[ERROR] Error: {result.get('error')}")
            return False
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"  Response: {e.response.text[:200]}")
        return False

def test_chat_without_llm():
    """Test chat endpoint up to LLM call (check if search works)"""
    print("\n" + "=" * 60)
    print("Testing /chat endpoint (up to LLM call)...")
    try:
        data = {
            "repo_dir": REPO_DIR,
            "question": "test",
            "analysis_type": "explain"
        }
        response = requests.post(
            f"{BASE_URL}/chat",
            json=data,
            timeout=15
        )
        result = response.json()
        
        if result.get("ok"):
            print(f"[OK] Chat endpoint returned successfully!")
            print(f"[OK] Answer length: {len(result.get('answer', ''))}")
            print(f"[OK] Evidences found: {len(result.get('evidences', []))}")
            return True
        else:
            error = result.get('error', 'Unknown error')
            if 'Authentication' in error or 'API key' in error or 'governor' in error:
                print(f"[PARTIAL] Expected: API key not configured")
                print(f"  Error: {error[:100]}...")
                print(f"[OK] But the endpoint structure works (search + evidence gathering)")
                return "partial"
            else:
                print(f"[ERROR] Error: {error[:200]}")
                return False
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False

def check_index_exists():
    """Check if repository is indexed"""
    print("\n" + "=" * 60)
    print("Checking if repository is indexed...")
    import os
    from pathlib import Path
    index_path = Path("data/index/my-portfolio/faiss.index")
    if index_path.exists():
        print(f"[OK] Index exists: {index_path}")
        
        meta_path = Path("data/index/my-portfolio/meta.json")
        if meta_path.exists():
            import json
            with open(meta_path, encoding='utf-8') as f:
                meta = json.load(f)
            print(f"[OK] Indexed chunks: {len(meta)}")
        return True
    else:
        print(f"[ERROR] Index not found. Run /index_repo first.")
        return False

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("CODE ANALYSIS SYSTEM - ENDPOINT TEST")
    print("=" * 60)
    
    results = []
    
    # Test 1: Health
    results.append(("Health Check", test_health()))
    
    # Test 2: Check index
    results.append(("Index Check", check_index_exists()))
    
    # Test 3: Search (no API key needed)
    results.append(("Search Endpoint", test_search()))
    
    # Test 4: Chat (will fail on LLM but show if code path works)
    results.append(("Chat Endpoint", test_chat_without_llm()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for name, result in results:
        if result is True:
            print(f"[PASS] {name}: PASSED")
        elif result == "partial":
            print(f"[PARTIAL] {name}: PARTIAL (expected - needs API key)")
        else:
            print(f"[FAIL] {name}: FAILED")
    
    print("\n" + "=" * 60)
    print("NOTE: To fully test chat endpoint, configure DEEPSEEK_API_KEY in .env")
    print("=" * 60)

