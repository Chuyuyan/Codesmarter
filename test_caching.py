"""
Test script for caching functionality.
Tests LLM response caching and search result caching.
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:5050"

def test_server_health():
    """Test if server is running."""
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
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_cache_stats():
    """Test cache statistics endpoint."""
    print("\n=== Testing Cache Statistics ===")
    try:
        response = requests.get(f"{BASE_URL}/cache/stats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                stats = data.get("stats", {})
                summary = data.get("summary", {})
                print(f"✅ Cache statistics retrieved")
                print(f"   Total entries: {summary.get('total_entries', 0)}")
                print(f"   Total size: {summary.get('total_size_mb', 0)} MB")
                print(f"   Total hits: {summary.get('total_hits', 0)}")
                print(f"   Total misses: {summary.get('total_misses', 0)}")
                
                print(f"\n   LLM Cache:")
                print(f"     Entries: {stats.get('llm', {}).get('total_entries', 0)}")
                print(f"     Hit rate: {stats.get('llm', {}).get('hit_rate', 0)}%")
                
                print(f"   Search Cache:")
                print(f"     Entries: {stats.get('search', {}).get('total_entries', 0)}")
                print(f"     Hit rate: {stats.get('search', {}).get('hit_rate', 0)}%")
                
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

def test_search_caching():
    """Test search result caching."""
    print("\n=== Testing Search Result Caching ===")
    
    # You'll need to provide a valid repo_dir and query
    repo_dir = input("Enter repository directory (or press Enter to skip): ").strip()
    if not repo_dir:
        print("⏭️  Skipping search cache test (no repo provided)")
        return True
    
    query = input("Enter search query (or press Enter for 'def'): ").strip() or "def"
    
    # First search (cache miss)
    print(f"\n1. First search (should be cache MISS)...")
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/search",
            json={"repo_dir": repo_dir, "query": query},
            timeout=30
        )
        first_duration = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                cached = data.get("cached", False)
                count = data.get("count", 0)
                print(f"   ✅ Search completed in {first_duration:.2f}s")
                print(f"   Results: {count}")
                print(f"   Cached: {cached} (expected: False)")
            else:
                print(f"   ❌ Error: {data.get('error')}")
                return False
        else:
            print(f"   ❌ Request failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Second search (cache hit - should be faster)
    print(f"\n2. Second search (should be cache HIT)...")
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/search",
            json={"repo_dir": repo_dir, "query": query},
            timeout=30
        )
        second_duration = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                cached = data.get("cached", False)
                count = data.get("count", 0)
                print(f"   ✅ Search completed in {second_duration:.2f}s")
                print(f"   Results: {count}")
                print(f"   Cached: {cached} (expected: True)")
                
                if cached:
                    print(f"   ✅ Cache working! ({first_duration:.2f}s → {second_duration:.2f}s)")
                    speedup = first_duration / second_duration if second_duration > 0 else 0
                    print(f"   ⚡ Speedup: {speedup:.2f}x")
                    return True
                else:
                    print(f"   ⚠️  Cache not working (expected cached=True)")
                    return False
            else:
                print(f"   ❌ Error: {data.get('error')}")
                return False
        else:
            print(f"   ❌ Request failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_cache_clear():
    """Test cache clear endpoint."""
    print("\n=== Testing Cache Clear ===")
    confirm = input("Clear all caches? (y/N): ").strip().lower()
    if confirm != 'y':
        print("⏭️  Skipping cache clear test")
        return True
    
    try:
        response = requests.post(
            f"{BASE_URL}/cache/clear",
            json={"cache_type": "all"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                cleared = data.get("cleared", {})
                print(f"✅ Caches cleared:")
                for cache_type, count in cleared.items():
                    print(f"   {cache_type}: {count} entries")
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
    """Test cache cleanup endpoint (remove expired entries)."""
    print("\n=== Testing Cache Cleanup ===")
    try:
        response = requests.post(f"{BASE_URL}/cache/cleanup", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                cleaned = data.get("cleaned", {})
                total = data.get("total_removed", 0)
                print(f"✅ Cleanup completed:")
                print(f"   Removed {total} expired entries")
                for cache_type, count in cleaned.items():
                    if count > 0:
                        print(f"   {cache_type}: {count} entries removed")
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

def main():
    """Run all tests."""
    print("=" * 60)
    print("Caching System Test Suite")
    print("=" * 60)
    
    if not test_server_health():
        print("\n❌ Server is not running. Please start it first:")
        print("   python -m backend.app")
        return
    
    results = []
    
    # Test cache stats
    results.append(("Cache Stats", test_cache_stats()))
    
    # Test cache cleanup (safe to run)
    results.append(("Cache Cleanup", test_cache_cleanup()))
    
    # Test search caching (optional)
    results.append(("Search Caching", test_search_caching()))
    
    # Test cache clear (optional)
    results.append(("Cache Clear", test_cache_clear()))
    
    # Final stats
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
        print("\n🎉 All tests passed! Caching system is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()

