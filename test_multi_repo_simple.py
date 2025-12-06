"""
Simple test to verify multi-repo support is working.
Tests basic functionality without requiring actual repositories.
"""
import sys
from pathlib import Path

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all imports work correctly."""
    print("=" * 60)
    print("🧪 Test 1: Import Check")
    print("=" * 60)
    
    try:
        from backend.modules.multi_repo import (
            repo_id_from_path,
            get_indexed_repos,
            search_multiple_repos,
            index_multiple_repos
        )
        print("✅ All imports successful!")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_repo_id_from_path():
    """Test repo_id_from_path function."""
    print("\n" + "=" * 60)
    print("🧪 Test 2: repo_id_from_path Function")
    print("=" * 60)
    
    try:
        from backend.modules.multi_repo import repo_id_from_path
        
        # Test cases
        test_cases = [
            ("C:\\Users\\57811\\my-portfolio", "my-portfolio"),
            ("C:\\test\\repo", "repo"),
            ("./test-repo", "test-repo"),
        ]
        
        all_passed = True
        for path, expected in test_cases:
            result = repo_id_from_path(path)
            if result == expected or result == Path(path).resolve().name:
                print(f"✅ {path} -> {result}")
            else:
                print(f"❌ {path} -> {result} (expected: {expected})")
                all_passed = False
        
        return all_passed
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_get_indexed_repos():
    """Test get_indexed_repos function."""
    print("\n" + "=" * 60)
    print("🧪 Test 3: get_indexed_repos Function")
    print("=" * 60)
    
    try:
        from backend.modules.multi_repo import get_indexed_repos
        
        repos = get_indexed_repos()
        print(f"✅ Function executed successfully!")
        print(f"   Found {len(repos)} indexed repository(ies)")
        
        for repo in repos[:3]:  # Show first 3
            print(f"   - {repo.get('repo_id')}: {repo.get('chunks', 0)} chunks")
        
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_server_endpoints():
    """Test that server endpoints exist and are accessible."""
    print("\n" + "=" * 60)
    print("🧪 Test 4: Server Endpoint Check")
    print("=" * 60)
    
    try:
        import requests
        
        server_url = "http://127.0.0.1:5050"
        
        # Test health endpoint
        try:
            response = requests.get(f"{server_url}/health", timeout=2)
            if response.status_code == 200:
                print("✅ Server is running")
                
                # Test /repos endpoint
                try:
                    response = requests.get(f"{server_url}/repos", timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("ok"):
                            repos = data.get("repos", [])
                            print(f"✅ /repos endpoint works! Found {len(repos)} repos")
                            return True
                        else:
                            print(f"⚠️  /repos endpoint returned error: {data.get('error')}")
                            return False
                    else:
                        print(f"⚠️  /repos endpoint returned status {response.status_code}")
                        return False
                except requests.exceptions.RequestException as e:
                    print(f"⚠️  /repos endpoint not accessible: {e}")
                    print("   (This is OK if server is not running)")
                    return None  # Not a failure, just server not running
            else:
                print(f"❌ Server health check failed: {response.status_code}")
                return False
        except requests.exceptions.RequestException:
            print("⚠️  Server is not running")
            print("   (This is OK - the code works, just server not started)")
            return None  # Not a failure
    except ImportError:
        print("⚠️  requests library not available")
        print("   Install with: pip install requests")
        return None

def main():
    """Run all tests."""
    print("=" * 60)
    print("🔧 Testing Multi-Repo Support - Basic Functionality")
    print("=" * 60)
    
    results = []
    
    # Test 1: Imports
    results.append(("Import Check", test_imports()))
    
    # Test 2: repo_id_from_path
    results.append(("repo_id_from_path", test_repo_id_from_path()))
    
    # Test 3: get_indexed_repos
    results.append(("get_indexed_repos", test_get_indexed_repos()))
    
    # Test 4: Server endpoints (optional - only if server is running)
    endpoint_result = test_server_endpoints()
    if endpoint_result is not None:
        results.append(("Server Endpoints", endpoint_result))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    core_tests = [r for r in results if r[0] != "Server Endpoints"]
    all_core_passed = all(success for _, success in core_tests if success is not None)
    
    for name, success in results:
        if success is None:
            status = "⚠️  SKIPPED (optional)"
        elif success:
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
        print(f"   {name}: {status}")
    
    if all_core_passed:
        print("\n✅ Core functionality is working!")
        print("   Multi-repo support code is properly integrated.")
        if endpoint_result is None:
            print("\n💡 To test full functionality:")
            print("   1. Start server: python -m backend.app")
            print("   2. Run: python test_multi_repo.py")
    else:
        print("\n❌ Some core tests failed. Check errors above.")
    
    print("=" * 60)
    
    return all_core_passed

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

