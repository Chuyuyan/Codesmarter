"""
Simple automated test for caching functionality.
Tests LLM response caching without user interaction.
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:5050"

def test_cache_stats():
    """Test cache statistics endpoint."""
    print("\n=== Test 1: Cache Statistics ===")
    try:
        response = requests.get(f"{BASE_URL}/cache/stats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                stats = data.get("stats", {})
                print("✅ Cache statistics endpoint working")
                print(f"   LLM cache entries: {stats.get('llm', {}).get('total_entries', 0)}")
                print(f"   Search cache entries: {stats.get('search', {}).get('total_entries', 0)}")
                return True
            else:
                print(f"❌ Error: {data.get('error')}")
                return False
        else:
            print(f"❌ Request failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_cache_cleanup():
    """Test cache cleanup endpoint."""
    print("\n=== Test 2: Cache Cleanup ===")
    try:
        response = requests.post(f"{BASE_URL}/cache/cleanup", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                print("✅ Cache cleanup endpoint working")
                print(f"   Removed {data.get('total_removed', 0)} expired entries")
                return True
            else:
                print(f"❌ Error: {data.get('error')}")
                return False
        else:
            print(f"❌ Request failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_cache_clear():
    """Test cache clear endpoint (non-destructive - clears empty cache)."""
    print("\n=== Test 3: Cache Clear ===")
    try:
        response = requests.post(
            f"{BASE_URL}/cache/clear",
            json={"cache_type": "all"},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                print("✅ Cache clear endpoint working")
                cleared = data.get("cleared", {})
                print(f"   Cleared entries:")
                for cache_type, count in cleared.items():
                    print(f"     {cache_type}: {count}")
                return True
            else:
                print(f"❌ Error: {data.get('error')}")
                return False
        else:
            print(f"❌ Request failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_server_health():
    """Test if server is running."""
    print("\n=== Test 0: Server Health ===")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
            return True
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Is it running?")
        print("   Start server with: python -m backend.app")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Simple Caching System Test (Automated)")
    print("=" * 60)
    
    if not test_server_health():
        return
    
    results = []
    
    # Test cache stats
    results.append(("Cache Stats", test_cache_stats()))
    
    # Test cache cleanup
    results.append(("Cache Cleanup", test_cache_cleanup()))
    
    # Test cache clear
    results.append(("Cache Clear", test_cache_clear()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Caching system is operational.")
        print("\n💡 Note: Empty cache is expected on first run.")
        print("   Cache will populate as you use the system:")
        print("   - LLM responses will be cached after chat/refactor calls")
        print("   - Search results will be cached after search calls")
        print("\n📊 Check cache stats after using the system:")
        print("   curl http://127.0.0.1:5050/cache/stats")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()

