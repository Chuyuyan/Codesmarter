"""
Test script for the direct code editing endpoint.
"""
import requests
import json

SERVER_URL = "http://127.0.0.1:5050"

def test_edit_code():
    """Test editing selected code."""
    print("\n=== Test: Direct Code Editing ===")
    
    selected_code = """def calculate_total(items):
    total = 0
    for item in items:
        total += item['price']
    return total"""
    
    instruction = "Add error handling for missing price key and validate input"
    
    response = requests.post(
        f"{SERVER_URL}/edit",
        json={
            "selected_code": selected_code,
            "instruction": instruction,
            "file_path": "test_file.py",
            "repo_dir": "C:\\Users\\57811\\my-portfolio"  # Adjust to your repo
        },
        timeout=120
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get("ok"):
            print("[PASS] Code edited successfully!")
            print(f"\nOriginal Code:")
            print(data.get("original_code", ""))
            print(f"\nEdited Code:")
            print(data.get("edited_code", ""))
            print(f"\nDiff:")
            print(data.get("diff", "")[:500] + "..." if len(data.get("diff", "")) > 500 else data.get("diff", ""))
            print(f"\nLanguage: {data.get('language')}")
            print(f"Lines added: {data.get('lines_added', 0)}")
            print(f"Lines removed: {data.get('lines_removed', 0)}")
            return True
        else:
            print(f"[FAIL] Error: {data.get('error')}")
            return False
    else:
        print(f"[FAIL] HTTP Error: {response.status_code}")
        print(f"Response: {response.text}")
        return False


def test_edit_with_context():
    """Test editing code with file context."""
    print("\n=== Test: Edit with File Context ===")
    
    selected_code = """def process_order(order):
    total = calculate_total(order['items'])
    return total"""
    
    file_context = """class OrderProcessor:
    def __init__(self):
        self.tax_rate = 0.1
    
    def process_order(self, order):
        total = calculate_total(order['items'])
        return total
    
    def apply_tax(self, amount):
        return amount * (1 + self.tax_rate)"""
    
    instruction = "Add error handling and apply tax to the total"
    
    response = requests.post(
        f"{SERVER_URL}/edit",
        json={
            "selected_code": selected_code,
            "instruction": instruction,
            "file_path": "order_processor.py",
            "file_context": file_context,
            "repo_dir": "C:\\Users\\57811\\my-portfolio"
        },
        timeout=120
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get("ok"):
            print("[PASS] Code edited with context!")
            print(f"Edited Code:\n{data.get('edited_code', '')}")
            return True
        else:
            print(f"[FAIL] Error: {data.get('error')}")
            return False
    else:
        print(f"[FAIL] HTTP Error: {response.status_code}")
        return False


def run_all_tests():
    """Run all direct edit tests."""
    print("=" * 60)
    print("DIRECT CODE EDITING ENDPOINT TEST SUITE")
    print("=" * 60)
    
    results = []
    
    # Test 1: Basic edit
    try:
        results.append(("Edit Code", test_edit_code()))
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        results.append(("Edit Code", False))
    
    # Test 2: Edit with context
    try:
        results.append(("Edit with Context", test_edit_with_context()))
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        results.append(("Edit with Context", False))
    
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
        print("\n[SUCCESS] All tests passed! Direct edit endpoint is working!")
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

