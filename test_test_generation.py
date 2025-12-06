"""
Test script for the test generation endpoint.
"""
import requests
import json

SERVER_URL = "http://127.0.0.1:5050"

def test_generate_tests_from_file():
    """Test generating tests from a file."""
    print("\n=== Test 1: Generate Tests from File ===")
    
    code_snippet = """def calculate_total(items):
    total = 0
    for item in items:
        if 'price' not in item:
            raise ValueError(f"Item missing 'price' key: {item}")
        total += item['price']
    return total"""
    
    response = requests.post(
        f"{SERVER_URL}/generate_tests",
        json={
            "code_snippet": code_snippet,
            "test_framework": "pytest",
            "test_type": "unit",
            "repo_dir": "C:\\Users\\57811\\my-portfolio"  # Adjust to your repo
        },
        timeout=180
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get("ok"):
            print("[PASS] Tests generated successfully!")
            print(f"Framework: {data.get('test_framework')}")
            print(f"Language: {data.get('language')}")
            print(f"Test Type: {data.get('test_type')}")
            print(f"Lines: {data.get('lines')}")
            print(f"\nGenerated Test Code:")
            print("=" * 60)
            print(data.get('test_code', '')[:1000])
            if len(data.get('test_code', '')) > 1000:
                print(f"\n... (truncated, total {len(data.get('test_code', ''))} chars)")
            print("=" * 60)
            return True
        else:
            print(f"[FAIL] Error: {data.get('error')}")
            return False
    else:
        print(f"[FAIL] HTTP Error: {response.status_code}")
        print(f"Response: {response.text}")
        return False


def test_generate_tests_auto_detect():
    """Test generating tests with auto-detected framework."""
    print("\n=== Test 2: Generate Tests with Auto-Detection ===")
    
    code_snippet = """class Calculator:
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        result = a + b
        self.history.append(('add', a, b, result))
        return result
    
    def subtract(self, a, b):
        result = a - b
        self.history.append(('subtract', a, b, result))
        return result
    
    def get_history(self):
        return self.history"""
    
    response = requests.post(
        f"{SERVER_URL}/generate_tests",
        json={
            "code_snippet": code_snippet,
            "test_type": "unit",
            "repo_dir": "C:\\Users\\57811\\my-portfolio"
        },
        timeout=180
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get("ok"):
            print("[PASS] Tests generated with auto-detection!")
            print(f"Detected Framework: {data.get('test_framework')}")
            print(f"Language: {data.get('language')}")
            print(f"Lines: {data.get('lines')}")
            return True
        else:
            print(f"[FAIL] Error: {data.get('error')}")
            return False
    else:
        print(f"[FAIL] HTTP Error: {response.status_code}")
        return False


def test_generate_integration_tests():
    """Test generating integration tests."""
    print("\n=== Test 3: Generate Integration Tests ===")
    
    code_snippet = """def process_order(order):
    if not order:
        return None
    total = calculate_total(order.get('items', []))
    if order.get('discount'):
        total *= (1 - order['discount'])
    return {
        'order_id': order.get('id'),
        'total': total,
        'status': 'processed'
    }"""
    
    response = requests.post(
        f"{SERVER_URL}/generate_tests",
        json={
            "code_snippet": code_snippet,
            "test_framework": "pytest",
            "test_type": "integration",
            "repo_dir": "C:\\Users\\57811\\my-portfolio"
        },
        timeout=180
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get("ok"):
            print("[PASS] Integration tests generated!")
            print(f"Test Type: {data.get('test_type')}")
            print(f"Lines: {data.get('lines')}")
            return True
        else:
            print(f"[FAIL] Error: {data.get('error')}")
            return False
    else:
        print(f"[FAIL] HTTP Error: {response.status_code}")
        return False


def run_all_tests():
    """Run all test generation tests."""
    print("=" * 60)
    print("TEST GENERATION ENDPOINT TEST SUITE")
    print("=" * 60)
    
    results = []
    
    # Test 1: Generate tests from code snippet
    try:
        results.append(("Generate Tests from Code", test_generate_tests_from_file()))
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        results.append(("Generate Tests from Code", False))
    
    # Test 2: Auto-detect framework
    try:
        results.append(("Auto-Detect Framework", test_generate_tests_auto_detect()))
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        results.append(("Auto-Detect Framework", False))
    
    # Test 3: Integration tests
    try:
        results.append(("Generate Integration Tests", test_generate_integration_tests()))
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        results.append(("Generate Integration Tests", False))
    
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
        print("\n[SUCCESS] All tests passed! Test generation endpoint is working!")
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

