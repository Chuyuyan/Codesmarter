"""
Test script for authentication API endpoints.
Tests the backend authentication system.
"""
import sys
import requests
import json
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
        print("       Start server with: python -m backend.app")
        return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False

def test_register():
    """Test user registration."""
    print("\n=== Testing User Registration ===")
    
    # Generate unique username for testing
    import random
    test_username = f"testuser_{random.randint(1000, 9999)}"
    test_email = f"{test_username}@test.com"
    test_password = "testpass123"
    
    try:
        response = requests.post(
            f"{API_BASE}/auth/register",
            json={
                "username": test_username,
                "email": test_email,
                "password": test_password
            },
            timeout=10
        )
        
        data = response.json()
        
        if response.status_code == 201 and data.get("ok"):
            print(f"[OK] User registered successfully")
            print(f"     Username: {test_username}")
            print(f"     Email: {test_email}")
            return test_username, test_password, data.get("user", {}).get("id")
        else:
            print(f"[FAIL] Registration failed: {data.get('error', 'Unknown error')}")
            return None, None, None
            
    except Exception as e:
        print(f"[FAIL] Registration error: {e}")
        return None, None, None

def test_register_duplicate():
    """Test duplicate registration (should fail)."""
    print("\n=== Testing Duplicate Registration (Should Fail) ===")
    
    # Try to register with same username
    try:
        response = requests.post(
            f"{API_BASE}/auth/register",
            json={
                "username": "testuser_duplicate",
                "email": "testuser_duplicate@test.com",
                "password": "testpass123"
            },
            timeout=10
        )
        
        # Register again with same username
        response2 = requests.post(
            f"{API_BASE}/auth/register",
            json={
                "username": "testuser_duplicate",
                "email": "testuser_duplicate2@test.com",
                "password": "testpass123"
            },
            timeout=10
        )
        
        data2 = response2.json()
        
        if response2.status_code == 400 and not data2.get("ok"):
            print("[OK] Duplicate registration correctly rejected")
            return True
        else:
            print("[FAIL] Duplicate registration should have been rejected")
            return False
            
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False

def test_login(username, password):
    """Test user login."""
    print("\n=== Testing User Login ===")
    
    if not username or not password:
        print("[SKIP] No credentials available (registration may have failed)")
        return None
    
    try:
        response = requests.post(
            f"{API_BASE}/auth/login",
            json={
                "username_or_email": username,
                "password": password
            },
            timeout=10
        )
        
        data = response.json()
        
        if response.status_code == 200 and data.get("ok"):
            token = data.get("token")
            print(f"[OK] Login successful")
            print(f"     Token received: {token[:20]}...")
            return token
        else:
            print(f"[FAIL] Login failed: {data.get('error', 'Unknown error')}")
            return None
            
    except Exception as e:
        print(f"[FAIL] Login error: {e}")
        return None

def test_login_invalid():
    """Test login with invalid credentials."""
    print("\n=== Testing Invalid Login (Should Fail) ===")
    
    try:
        response = requests.post(
            f"{API_BASE}/auth/login",
            json={
                "username_or_email": "nonexistent_user",
                "password": "wrongpassword"
            },
            timeout=10
        )
        
        data = response.json()
        
        if response.status_code == 401 and not data.get("ok"):
            print("[OK] Invalid login correctly rejected")
            return True
        else:
            print("[FAIL] Invalid login should have been rejected")
            return False
            
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False

def test_get_current_user(token):
    """Test getting current user info."""
    print("\n=== Testing Get Current User ===")
    
    if not token:
        print("[SKIP] No token available (login may have failed)")
        return False
    
    try:
        response = requests.get(
            f"{API_BASE}/auth/me",
            headers={
                "Authorization": f"Bearer {token}"
            },
            timeout=10
        )
        
        data = response.json()
        
        if response.status_code == 200 and data.get("ok"):
            user = data.get("user", {})
            print(f"[OK] User info retrieved")
            print(f"     Username: {user.get('username')}")
            print(f"     Email: {user.get('email')}")
            return True
        else:
            print(f"[FAIL] Failed to get user info: {data.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False

def test_get_current_user_no_token():
    """Test getting user info without token (should fail)."""
    print("\n=== Testing Get Current User Without Token (Should Fail) ===")
    
    try:
        response = requests.get(
            f"{API_BASE}/auth/me",
            timeout=10
        )
        
        if response.status_code == 401:
            print("[OK] Request without token correctly rejected")
            return True
        else:
            print(f"[FAIL] Request should have been rejected (got {response.status_code})")
            return False
            
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False

def test_update_user(token):
    """Test updating user profile."""
    print("\n=== Testing Update User Profile ===")
    
    if not token:
        print("[SKIP] No token available")
        return False
    
    try:
        # Update email
        response = requests.put(
            f"{API_BASE}/auth/me",
            headers={
                "Authorization": f"Bearer {token}"
            },
            json={
                "email": "updated_email@test.com"
            },
            timeout=10
        )
        
        data = response.json()
        
        if response.status_code == 200 and data.get("ok"):
            print("[OK] User profile updated")
            return True
        else:
            print(f"[FAIL] Update failed: {data.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False

def test_logout(token):
    """Test logout (token should still work, but we can verify it's stored)."""
    print("\n=== Testing Logout ===")
    print("[NOTE] Logout is client-side (token deletion).")
    print("       Token will still be valid until expiration.")
    print("[OK] Logout is handled by client (extension)")
    return True

def main():
    """Run all authentication tests."""
    print("=" * 60)
    print("Authentication API Test Suite")
    print("=" * 60)
    
    # Test server health
    if not test_server_health():
        print("\n[ERROR] Server is not running. Please start it first:")
        print("        python -m backend.app")
        print("\nOr use:")
        print("        python start_server.py")
        return
    
    results = []
    
    # Test registration
    username, password, user_id = test_register()
    results.append(("Registration", username is not None))
    
    # Test duplicate registration
    results.append(("Duplicate Registration", test_register_duplicate()))
    
    # Test login
    token = test_login(username, password)
    results.append(("Login", token is not None))
    
    # Test invalid login
    results.append(("Invalid Login Rejection", test_login_invalid()))
    
    # Test get current user
    results.append(("Get Current User", test_get_current_user(token)))
    
    # Test get current user without token
    results.append(("Get User Without Token", test_get_current_user_no_token()))
    
    # Test update user
    results.append(("Update User", test_update_user(token)))
    
    # Test logout (client-side)
    results.append(("Logout", test_logout(token)))
    
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

