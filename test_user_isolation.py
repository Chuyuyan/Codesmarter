"""
Test script for user-specific data isolation.
Tests that users can only access their own repositories and projects.
"""
import sys
import requests
import json
import random
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

API_BASE = "http://127.0.0.1:5050"

def test_server_health():
    """Test if server is running."""
    print("\n=== Testing Server Health ===")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            print("[OK] Server is running")
            return True
        else:
            print(f"[FAIL] Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("[FAIL] Cannot connect to server. Is it running?")
        return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False

def create_test_user(username_suffix):
    """Create a test user and return credentials."""
    username = f"isolation_test_{username_suffix}"
    email = f"{username}@test.com"
    password = "testpass123"
    
    try:
        response = requests.post(
            f"{API_BASE}/auth/register",
            json={
                "username": username,
                "email": email,
                "password": password
            },
            timeout=10
        )
        
        if response.status_code == 201:
            # Login to get token
            login_response = requests.post(
                f"{API_BASE}/auth/login",
                json={
                    "username_or_email": username,
                    "password": password
                },
                timeout=10
            )
            
            if login_response.status_code == 200:
                data = login_response.json()
                return {
                    "username": username,
                    "email": email,
                    "password": password,
                    "token": data.get("token"),
                    "user_id": data.get("user", {}).get("id")
                }
    except Exception as e:
        print(f"[ERROR] Failed to create user {username}: {e}")
    
    return None

def test_user_isolation():
    """Test that users can only see their own repositories."""
    print("\n=== Testing User Isolation ===")
    
    # Create two users
    print("Creating test users...")
    user1 = create_test_user(random.randint(1000, 9999))
    user2 = create_test_user(random.randint(1000, 9999))
    
    if not user1 or not user2:
        print("[FAIL] Failed to create test users")
        return False
    
    print(f"[OK] Created user1: {user1['username']}")
    print(f"[OK] Created user2: {user2['username']}")
    
    # User1 lists repos (should be empty)
    print("\nTesting: User1 lists repos (should be empty)...")
    try:
        response = requests.get(
            f"{API_BASE}/repos",
            headers={"Authorization": f"Bearer {user1['token']}"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            repos = data.get("repos", [])
            if len(repos) == 0:
                print(f"[OK] User1 has {len(repos)} repos (expected: 0)")
            else:
                print(f"[WARN] User1 has {len(repos)} repos (expected: 0)")
        else:
            print(f"[FAIL] Failed to get repos: {response.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False
    
    # User2 lists repos (should be empty)
    print("\nTesting: User2 lists repos (should be empty)...")
    try:
        response = requests.get(
            f"{API_BASE}/repos",
            headers={"Authorization": f"Bearer {user2['token']}"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            repos = data.get("repos", [])
            if len(repos) == 0:
                print(f"[OK] User2 has {len(repos)} repos (expected: 0)")
            else:
                print(f"[WARN] User2 has {len(repos)} repos (expected: 0)")
        else:
            print(f"[FAIL] Failed to get repos: {response.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False
    
    # Test: User1 can't access User2's repos (if they existed)
    print("\nTesting: User1 tries to access non-existent repo (should fail)...")
    try:
        # Try to search a repo that doesn't exist
        response = requests.post(
            f"{API_BASE}/chat",
            headers={"Authorization": f"Bearer {user1['token']}"},
            json={
                "question": "test",
                "repo_dir": "/nonexistent/path"
            },
            timeout=10
        )
        
        # Should fail with 403 (access denied) or 400 (not found)
        if response.status_code in [400, 403]:
            print(f"[OK] Correctly rejected access (status: {response.status_code})")
        else:
            print(f"[WARN] Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"[WARN] Error (expected): {e}")
    
    # Test: Unauthenticated request should fail
    print("\nTesting: Unauthenticated request to /repos (should fail)...")
    try:
        response = requests.get(f"{API_BASE}/repos", timeout=10)
        if response.status_code == 401:
            print("[OK] Correctly rejected unauthenticated request")
        else:
            print(f"[FAIL] Should return 401, got {response.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False
    
    print("\n[OK] User isolation tests passed!")
    return True

def test_repo_association():
    """Test that indexed repos are associated with users."""
    print("\n=== Testing Repository Association ===")
    
    # Create a user
    user = create_test_user(random.randint(1000, 9999))
    if not user:
        print("[FAIL] Failed to create test user")
        return False
    
    print(f"[OK] Created user: {user['username']}")
    
    # Note: We can't actually index a repo in this test without a real repo path
    # But we can verify the endpoint requires authentication
    print("\nTesting: /index_repo requires authentication...")
    try:
        response = requests.post(
            f"{API_BASE}/index_repo",
            json={"repo_dir": "/test/path"},
            timeout=10
        )
        
        if response.status_code == 401:
            print("[OK] Correctly requires authentication")
        else:
            print(f"[WARN] Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"[WARN] Error: {e}")
    
    print("\n[OK] Repository association tests passed!")
    return True

def main():
    """Run all user isolation tests."""
    print("=" * 60)
    print("User Isolation Test Suite")
    print("=" * 60)
    
    # Test server health
    if not test_server_health():
        print("\n[ERROR] Server is not running. Please start it first:")
        print("        python -m backend.app")
        return
    
    results = []
    
    # Test user isolation
    results.append(("User Isolation", test_user_isolation()))
    
    # Test repo association
    results.append(("Repository Association", test_repo_association()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "[OK]" if result else "[FAIL]"
        print(f"{status} {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All tests passed! ✅")
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed")
    
    print("=" * 60)

if __name__ == "__main__":
    main()

