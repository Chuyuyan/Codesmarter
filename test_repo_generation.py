"""
Test script for repository generation endpoint.
Tests generating entire repositories from scratch.
"""
import requests
import json
import time
import os
import shutil
from pathlib import Path

BASE_URL = "http://127.0.0.1:5050"
TEST_REPO_BASE = Path("test_generated_repos")

def test_server_health():
    """Test if server is running."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("[PASS] Server is running")
            return True
        else:
            print(f"[FAIL] Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("[FAIL] Cannot connect to server. Is it running?")
        print("   Start server with: python -m backend.app")
        return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False

def cleanup_test_repo(repo_path: str):
    """Clean up test repository."""
    try:
        repo_path_obj = Path(repo_path)
        if repo_path_obj.exists():
            shutil.rmtree(repo_path_obj)
            print(f"   [OK] Cleaned up test repo: {repo_path}")
    except Exception as e:
        print(f"   [WARN] Warning: Could not clean up {repo_path}: {e}")

def test_generate_repo_preview():
    """Test repository generation in preview mode (dry_run)."""
    print("\n=== Test 1: Repository Generation Preview ===")
    
    repo_path = str(TEST_REPO_BASE / "preview_test")
    
    # Clean up if exists
    cleanup_test_repo(repo_path)
    
    try:
        print(f"   Generating preview for: Simple Python calculator app")
        print(f"   Target path: {repo_path}")
        
        response = requests.post(
            f"{BASE_URL}/generate_repo",
            json={
                "description": "Create a simple Python calculator app with add, subtract, multiply, and divide functions",
                "repo_path": repo_path,
                "dry_run": True,  # Preview only
                "apply": False
            },
            timeout=120  # 2 minutes timeout
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                print("   [PASS] Repository generation preview successful")
                print(f"   Project type: {data.get('project_type')}")
                print(f"   Language: {data.get('language')}")
                print(f"   Files to create: {data.get('total_files', 0)}")
                print(f"   Directories to create: {data.get('total_directories', 0)}")
                
                if data.get("summary"):
                    print(f"   Summary: {data.get('summary')[:100]}...")
                
                if data.get("files"):
                    print(f"   Sample files:")
                    for file_info in data.get("files", [])[:5]:  # Show first 5
                        print(f"     - {file_info.get('path')} ({file_info.get('lines', 0)} lines)")
                
                if data.get("dependencies"):
                    print(f"   Dependencies: {', '.join(data.get('dependencies', [])[:5])}")
                
                return True
            else:
                print(f"   ❌ Error: {data.get('error')}")
                return False
        else:
            print(f"   ❌ Request failed with status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_generate_repo_create():
    """Test actually creating a repository."""
    print("\n=== Test 2: Repository Generation (Create Files) ===")
    
    repo_path = str(TEST_REPO_BASE / "create_test")
    
    # Clean up if exists
    cleanup_test_repo(repo_path)
    
    try:
        print(f"   Creating repository: Simple Python todo app")
        print(f"   Target path: {repo_path}")
        
        response = requests.post(
            f"{BASE_URL}/generate_repo",
            json={
                "description": "Create a simple Python todo app with a Todo class, add, remove, and list functions. Include a main.py file and README.",
                "repo_path": repo_path,
                "dry_run": False,
                "apply": True  # Actually create files
            },
            timeout=180  # 3 minutes timeout (can take longer for full generation)
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                print("   [PASS] Repository created successfully!")
                print(f"   Files created: {data.get('total_files', 0)}")
                print(f"   Directories created: {data.get('total_directories', 0)}")
                
                # Verify files actually exist
                repo_path_obj = Path(repo_path)
                if repo_path_obj.exists():
                    files = list(repo_path_obj.rglob("*"))
                    actual_files = [f for f in files if f.is_file()]
                    actual_dirs = [f for f in files if f.is_dir()]
                    
                    print(f"   [PASS] Verified: {len(actual_files)} files exist on disk")
                    print(f"   [PASS] Verified: {len(actual_dirs)} directories exist on disk")
                    
                    if actual_files:
                        print(f"   Sample files on disk:")
                        for file_path in actual_files[:5]:
                            relative_path = file_path.relative_to(repo_path_obj)
                            size = file_path.stat().st_size
                            print(f"     - {relative_path} ({size} bytes)")
                    
                    return True
                else:
                    print(f"   [FAIL] Repository directory not created")
                    return False
            else:
                print(f"   [FAIL] Error: {data.get('error')}")
                return False
        else:
            print(f"   [FAIL] Request failed with status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    
    except Exception as e:
        print(f"   [FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_generate_repo_project_types():
    """Test different project types."""
    print("\n=== Test 3: Project Type Detection ===")
    
    test_cases = [
        ("Create a Next.js todo app with TypeScript", "nextjs", "typescript"),
        ("Create a React application", "react", "javascript"),
        ("Create a Flask web API", "flask", "python"),
        ("Create a Python script", "python", "python")
    ]
    
    results = []
    for description, expected_type, expected_lang in test_cases:
        try:
            from backend.modules.repo_generator import detect_project_type
            detected_type, detected_lang = detect_project_type(description)
            
            type_match = detected_type == expected_type or expected_type in detected_type
            lang_match = detected_lang == expected_lang
            
            if type_match and lang_match:
                print(f"   [PASS] '{description[:40]}...' -> {detected_type}/{detected_lang}")
                results.append(True)
            else:
                print(f"   [WARN] '{description[:40]}...' -> {detected_type}/{detected_lang} (expected {expected_type}/{expected_lang})")
                results.append(False)
        except Exception as e:
            print(f"   [FAIL] Error detecting type: {e}")
            results.append(False)
    
    return all(results)

def main():
    """Run all tests."""
    print("=" * 60)
    print("Repository Generation Test Suite")
    print("=" * 60)
    
    if not test_server_health():
        print("\n[FAIL] Server is not running. Please start it first:")
        print("   python -m backend.app")
        return
    
    # Create test repos directory
    TEST_REPO_BASE.mkdir(exist_ok=True)
    
    results = []
    
    # Test 1: Preview mode
    results.append(("Preview Mode", test_generate_repo_preview()))
    
    # Test 2: Create mode (optional - user can skip)
    print("\n" + "=" * 60)
    create_choice = input("Test actual file creation? This will create files on disk. (y/N): ").strip().lower()
    if create_choice == 'y':
        results.append(("Create Files", test_generate_repo_create()))
    else:
        print("[SKIP] Skipping file creation test")
        results.append(("Create Files", None))  # Skipped
    
    # Test 3: Project type detection
    results.append(("Project Type Detection", test_generate_repo_project_types()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result is True)
    failed = sum(1 for _, result in results if result is False)
    skipped = sum(1 for _, result in results if result is None)
    total = len(results)
    
    for test_name, result in results:
        if result is True:
            status = "[PASS]"
        elif result is False:
            status = "[FAIL]"
        else:
            status = "[SKIP]"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total - skipped} tests passed ({skipped} skipped)")
    
    # Cleanup option
    print("\n" + "=" * 60)
    cleanup_choice = input("Clean up test repositories? (y/N): ").strip().lower()
    if cleanup_choice == 'y':
        if TEST_REPO_BASE.exists():
            try:
                shutil.rmtree(TEST_REPO_BASE)
                print(f"[OK] Cleaned up {TEST_REPO_BASE}")
            except Exception as e:
                print(f"[WARN] Could not clean up: {e}")
    
    if passed == total - skipped:
        print("\n[SUCCESS] All tests passed! Repository generation is working correctly.")
    else:
        print("\n[WARN] Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()

