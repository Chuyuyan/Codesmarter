#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for both upload methods:
1. File upload (ZIP)
2. Git URL clone

Run this after starting the server and logging in via web UI to get auth token.
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

API_BASE = "http://127.0.0.1:5050"
TEST_ZIP = "test_project.zip"
TEST_GIT_URL = "https://github.com/octocat/Hello-World"  # Small public repo for testing

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_server_connection():
    """Test if server is running"""
    try:
        response = requests.get(f"{API_BASE}/", timeout=3)
        return response.status_code == 200
    except:
        return False

def test_file_upload(token):
    """Test 1: File upload (ZIP)"""
    print_header("TEST 1: File Upload (ZIP)")
    
    if not os.path.exists(TEST_ZIP):
        print(f"[X] Error: {TEST_ZIP} not found!")
        return False
    
    file_size = os.path.getsize(TEST_ZIP) / 1024  # KB
    print(f"[FILE] Test file: {TEST_ZIP}")
    print(f"       Size: {file_size:.2f} KB")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\n[UPLOAD] Uploading {TEST_ZIP}...")
    
    try:
        with open(TEST_ZIP, 'rb') as f:
            files = {'file': (TEST_ZIP, f, 'application/zip')}
            data = {'repo_name': 'test-upload-zip'}
            
            response = requests.post(
                f"{API_BASE}/upload_and_index",
                headers=headers,
                files=files,
                data=data,
                timeout=300
            )
        
        print(f"[STATUS] Response: {response.status_code}")
        
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
            result = response.json() if 'application/json' in response.headers.get('content-type', '') else {}
            print(f"[X] Failed: {result.get('error', response.text[:200])}")
            return False
            
    except requests.exceptions.Timeout:
        print("[X] Request timeout (file too large or server slow)")
        return False
    except Exception as e:
        print(f"[X] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_git_clone(token):
    """Test 2: Git URL clone"""
    print_header("TEST 2: Git URL Clone")
    
    print(f"[GIT] Repository URL: {TEST_GIT_URL}")
    print(f"      This is a small public repository for testing")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "git_url": TEST_GIT_URL,
        "repo_name": "test-clone-hello-world"
    }
    
    print(f"\n[CLONE] Cloning repository...")
    print(f"        This may take 1-2 minutes...")
    
    try:
        response = requests.post(
            f"{API_BASE}/clone_and_index",
            headers=headers,
            json=payload,
            timeout=300  # 5 minutes
        )
        
        print(f"[STATUS] Response: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("[OK] Clone successful!")
                print(f"     Repository ID: {result.get('repo_id')}")
                print(f"     Chunks: {result.get('chunks')}")
                print(f"     Path: {result.get('cloned_path')}")
                print(f"     Git URL: {result.get('git_url')}")
                return True
            else:
                print(f"[X] Clone failed: {result.get('error')}")
                return False
        elif response.status_code == 408:
            print("[X] Clone timed out (repository may be too large)")
            return False
        else:
            result = response.json() if 'application/json' in response.headers.get('content-type', '') else {}
            error_msg = result.get('error', response.text[:200])
            print(f"[X] Failed: {error_msg}")
            return False
            
    except requests.exceptions.Timeout:
        print("[X] Request timeout (clone or indexing taking too long)")
        return False
    except Exception as e:
        print(f"[X] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("=" * 70)
    print("  Testing Both Upload Methods")
    print("=" * 70)
    print("\nThis script tests:")
    print("  1. File Upload (ZIP)")
    print("  2. Git URL Clone")
    
    # Check server
    print("\n[1] Checking server connection...")
    if not test_server_connection():
        print("[X] Server is not running!")
        print("\nPlease start the server first:")
        print("  python -m backend.app")
        return 1
    
    print("[OK] Server is running")
    
    # Get auth token
    print("\n[2] Authentication required")
    print("    To get your auth token:")
    print("    1. Open browser: http://127.0.0.1:5050/")
    print("    2. Login to your account")
    print("    3. Open browser console (F12)")
    print("    4. Run: localStorage.getItem('authToken')")
    print("    5. Copy the token\n")
    
    token = input("Enter your auth token (or press Enter to skip): ").strip()
    
    if not token:
        print("\n[!] No token provided. Skipping authenticated tests.")
        print("    You can still test via web UI:")
        print("    - File Upload: http://127.0.0.1:5050/")
        print("    - Git Clone: http://127.0.0.1:5050/")
        return 0
    
    # Check test files
    print("\n[3] Checking test files...")
    if not os.path.exists(TEST_ZIP):
        print(f"[X] Test ZIP file not found: {TEST_ZIP}")
        print("    Please create it first or use web UI to upload")
        return 1
    
    file_size = os.path.getsize(TEST_ZIP) / 1024  # KB
    print(f"[OK] Test ZIP file: {TEST_ZIP} ({file_size:.2f} KB)")
    print(f"[OK] Test Git URL: {TEST_GIT_URL}")
    
    # Run tests
    results = []
    
    # Test 1: File Upload
    result1 = test_file_upload(token)
    results.append(("File Upload (ZIP)", result1))
    
    # Wait a bit between tests
    print("\n[WAIT] Waiting 3 seconds before next test...")
    import time
    time.sleep(3)
    
    # Test 2: Git Clone
    result2 = test_git_clone(token)
    results.append(("Git URL Clone", result2))
    
    # Summary
    print_header("Test Summary")
    
    for test_name, result in results:
        if result:
            status = "[PASS]"
            color = "OK"
        else:
            status = "[FAIL]"
            color = "X"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All tests passed!")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

