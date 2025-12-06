"""
Test script for the multi-file editing (Composer) endpoint.
"""
import requests
import json

SERVER_URL = "http://127.0.0.1:5050"

def test_compose_preview():
    """Test composing multi-file edits (preview only)."""
    print("\n=== Test 1: Compose Multi-File Edit (Preview) ===")
    
    response = requests.post(
        f"{SERVER_URL}/compose",
        json={
            "request": "Add error handling to all functions in the codebase that process user input",
            "repo_dir": "C:\\Users\\57811\\my-portfolio",  # Adjust to your repo
            "dry_run": True,
            "apply": False
        },
        timeout=120
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get("ok"):
            print("[PASS] Multi-file edit composed successfully!")
            print(f"Total files to edit: {data.get('total_files', 0)}")
            print(f"Summary: {data.get('summary', 'N/A')}")
            print(f"\nEdits:")
            for i, edit in enumerate(data.get("edits", []), 1):
                print(f"\n{i}. File: {edit.get('file')}")
                print(f"   Action: {edit.get('action')}")
                print(f"   Description: {edit.get('description', 'N/A')}")
                print(f"   Lines added: {edit.get('lines_added', 0)}")
                print(f"   Lines removed: {edit.get('lines_removed', 0)}")
                if edit.get('diff'):
                    print(f"   Diff preview:\n{edit.get('diff')[:300]}...")
            return True
        else:
            print(f"❌ Error: {data.get('error')}")
            return False
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        print(f"Response: {response.text}")
        return False


def test_compose_specific_files():
    """Test composing edits for specific files."""
    print("\n=== Test 2: Compose Edit for Specific Files ===")
    
    response = requests.post(
        f"{SERVER_URL}/compose",
        json={
            "request": "Add type hints to all function parameters and return types",
            "repo_dir": "C:\\Users\\57811\\my-portfolio",
            "target_files": ["app/contact/page.tsx", "app/experience/page.tsx"],  # Adjust to your files
            "dry_run": True,
            "apply": False
        },
        timeout=120
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get("ok"):
            print("[PASS] Edit composed for specific files!")
            print(f"Files to edit: {data.get('total_files', 0)}")
            for edit in data.get("edits", []):
                print(f"  - {edit.get('file')}: {edit.get('action')}")
            return True
        else:
            print(f"❌ Error: {data.get('error')}")
            return False
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        return False


def test_compose_apply():
    """Test composing and applying edits (WARNING: modifies files!)."""
    print("\n=== Test 3: Compose and Apply Edits (DRY RUN) ===")
    print("[INFO] This test runs in preview mode (dry_run=true) for safety")
    
    response = requests.post(
        f"{SERVER_URL}/compose",
        json={
            "request": "Add a comment at the top of each file explaining its purpose",
            "repo_dir": "C:\\Users\\57811\\my-portfolio",
            "target_files": ["app/contact/page.tsx"],  # Single file for testing
            "dry_run": True,  # Preview only
            "apply": False
        },
        timeout=120
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get("ok"):
            print("[PASS] Edit composed!")
            print("[INFO] Preview mode - no changes applied")
            print("To apply changes, set dry_run=false and apply=true")
            return True
        else:
            print(f"❌ Error: {data.get('error')}")
            return False
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        return False


def run_all_tests():
    """Run all compose tests."""
    print("=" * 60)
    print("MULTI-FILE EDITING (COMPOSER) ENDPOINT TEST SUITE")
    print("=" * 60)
    
    results = []
    
    # Test 1: Preview multi-file edit
    try:
        results.append(("Compose Preview", test_compose_preview()))
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        results.append(("Compose Preview", False))
    
    # Test 2: Specific files
    try:
        results.append(("Compose Specific Files", test_compose_specific_files()))
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        results.append(("Compose Specific Files", False))
    
    # Test 3: Apply (preview mode)
    try:
        results.append(("Compose Apply (Preview)", test_compose_apply()))
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        results.append(("Compose Apply (Preview)", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} - {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All tests passed! Composer endpoint is working!")
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed.")


if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\n[FAIL] Unexpected error: {e}")
        import traceback
        traceback.print_exc()

