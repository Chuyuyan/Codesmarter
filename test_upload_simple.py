#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test script for file upload API endpoint
Tests without requiring authentication token
"""
import requests
import os
import sys
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# Test configuration
API_BASE = "http://127.0.0.1:5050"
TEST_ZIP = "test_project.zip"

def test_server_connection():
    """Test if server is running"""
    try:
        response = requests.get(f"{API_BASE}/", timeout=3)
        return response.status_code == 200
    except:
        return False

def test_upload_without_auth():
    """Test upload without auth (should fail with 401)"""
    print("\n" + "=" * 60)
    print("Test 1: Upload without authentication (should fail)")
    print("=" * 60)
    
    if not os.path.exists(TEST_ZIP):
        print(f"❌ Error: {TEST_ZIP} not found!")
        return False
    
    try:
        with open(TEST_ZIP, 'rb') as f:
            files = {'file': (TEST_ZIP, f, 'application/zip')}
            data = {'repo_name': 'test-project'}
            
            response = requests.post(
                f"{API_BASE}/upload_and_index",
                files=files,
                data=data,
                timeout=10
            )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print("[OK] Correctly rejected (401 Unauthorized)")
            return True
        else:
            print(f"[X] Unexpected status: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("[X] Connection error: Server not running?")
        return False
    except Exception as e:
        print(f"[X] Error: {e}")
        return False

def test_upload_with_auth():
    """Test upload with auth token"""
    print("\n" + "=" * 60)
    print("Test 2: Upload with authentication")
    print("=" * 60)
    
    if not os.path.exists(TEST_ZIP):
        print(f"❌ Error: {TEST_ZIP} not found!")
        return False
    
    # Try to get token from environment or prompt
    token = os.getenv('AUTH_TOKEN', '').strip()
    
    if not token:
        print("\n[!] No authentication token provided")
        print("   To test with auth, you need to:")
        print("   1. Login via web UI: http://127.0.0.1:5050/")
        print("   2. Open browser console (F12)")
        print("   3. Run: localStorage.getItem('authToken')")
        print("   4. Set environment variable: $env:AUTH_TOKEN='your-token'")
        print("   5. Or run this script and enter token when prompted")
        print("\n   Skipping authenticated test...")
        return None
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"[UPLOAD] Uploading {TEST_ZIP}...")
    
    try:
        with open(TEST_ZIP, 'rb') as f:
            files = {'file': (TEST_ZIP, f, 'application/zip')}
            data = {'repo_name': 'test-project-api'}
            
            response = requests.post(
                f"{API_BASE}/upload_and_index",
                headers=headers,
                files=files,
                data=data,
                timeout=300  # 5 minutes for indexing
            )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("[OK] Upload successful!")
                print(f"     Repository ID: {result.get('repo_id')}")
                print(f"     Chunks: {result.get('chunks')}")
                print(f"     Path: {result.get('extracted_path')}")
                return True
            else:
                print(f"[X] Upload failed: {result.get('error')}")
                return False
        else:
            result = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            print(f"[X] Failed: {result.get('error', response.text[:200])}")
            return False
            
    except requests.exceptions.Timeout:
        print("[X] Request timeout (indexing may take time)")
        return False
    except Exception as e:
        print(f"[X] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("File Upload API Test Suite")
    print("=" * 60)
    
    # Check server
    print("\n[1] Checking server connection...")
    if not test_server_connection():
        print("[X] Server is not running!")
        print("\nPlease start the server first:")
        print("  python -m backend.app")
        return 1
    
    print("[OK] Server is running")
    
    # Check test file
    if not os.path.exists(TEST_ZIP):
        print(f"\n[X] Test file not found: {TEST_ZIP}")
        return 1
    
    file_size = os.path.getsize(TEST_ZIP) / 1024  # KB
    print(f"\n[FILE] Test file: {TEST_ZIP}")
    print(f"       Size: {file_size:.2f} KB")
    
    # Run tests
    results = []
    
    # Test 1: Without auth (should fail)
    result1 = test_upload_without_auth()
    results.append(("No Auth Test", result1))
    
    # Test 2: With auth (if token provided)
    result2 = test_upload_with_auth()
    if result2 is not None:
        results.append(("Auth Test", result2))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, result in results:
        if result is None:
            status = "[SKIP] Skipped"
        elif result:
            status = "[PASS] Passed"
        else:
            status = "[FAIL] Failed"
        print(f"{test_name}: {status}")
    
    # Return exit code
    failed = any(r is False for _, r in results if r is not None)
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main())

