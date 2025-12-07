#!/usr/bin/env python3
"""
Test script for file upload API endpoint
"""
import requests
import os
import sys
from pathlib import Path

# Test configuration
API_BASE = "http://127.0.0.1:5050"
TEST_ZIP = "test_project.zip"

def test_upload():
    """Test the upload_and_index endpoint"""
    
    print("=" * 60)
    print("Testing File Upload API")
    print("=" * 60)
    
    # Check if ZIP file exists
    if not os.path.exists(TEST_ZIP):
        print(f"❌ Error: {TEST_ZIP} not found!")
        print("   Please create a test ZIP file first.")
        return False
    
    # Check file size
    file_size = os.path.getsize(TEST_ZIP) / (1024 * 1024)  # MB
    print(f"\n📦 Test file: {TEST_ZIP}")
    print(f"   Size: {file_size:.2f} MB")
    
    if file_size > 100:
        print("⚠️  Warning: File exceeds 100MB limit")
    
    # Get auth token (you need to login first and get token)
    print("\n🔐 Authentication required")
    print("   Please login via web UI first, then:")
    print("   1. Open browser console (F12)")
    print("   2. Run: localStorage.getItem('authToken')")
    print("   3. Copy the token")
    
    token = input("\nEnter your auth token (or press Enter to skip auth test): ").strip()
    
    if not token:
        print("⚠️  Skipping authenticated test")
        print("   Testing without auth (should fail with 401)...")
        headers = {}
    else:
        headers = {
            "Authorization": f"Bearer {token}"
        }
    
    # Prepare file upload
    print(f"\n📤 Uploading {TEST_ZIP}...")
    
    try:
        with open(TEST_ZIP, 'rb') as f:
            files = {
                'file': (TEST_ZIP, f, 'application/zip')
            }
            data = {
                'repo_name': 'test-project-api'
            }
            
            response = requests.post(
                f"{API_BASE}/upload_and_index",
                headers=headers,
                files=files,
                data=data,
                timeout=300  # 5 minutes for large files
            )
        
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ Upload successful!")
                print(f"   Repository ID: {result.get('repo_id')}")
                print(f"   Chunks: {result.get('chunks')}")
                print(f"   Path: {result.get('extracted_path')}")
                return True
            else:
                print(f"❌ Upload failed: {result.get('error')}")
                return False
        elif response.status_code == 401:
            print("❌ Authentication failed (401)")
            print("   Please login and get a valid token")
            return False
        elif response.status_code == 400:
            result = response.json()
            print(f"❌ Bad request: {result.get('error')}")
            return False
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error: Server not running?")
        print(f"   Make sure server is running at {API_BASE}")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timeout (file too large or server slow)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_upload()
    sys.exit(0 if success else 1)

