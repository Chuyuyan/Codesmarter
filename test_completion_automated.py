"""
Automated test suite for inline code completion endpoint.
Tests various scenarios programmatically.
"""
import requests
import json
import time
import sys
from pathlib import Path

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SERVER_URL = "http://127.0.0.1:5050"

def test_health():
    """Test if server is running."""
    print("\n=== Test 1: Server Health Check ===")
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        return False


def test_basic_completion():
    """Test basic completion scenario."""
    print("\n=== Test 2: Basic Completion ===")
    
    file_content = """def calculate_total(items):
    total = 0
    for item in items:
        total += item['price']
    return total

def process_order(order):
    # TODO: implement order processing
    """
    
    try:
        response = requests.post(
            f"{SERVER_URL}/completion",
            json={
                "file_path": "test_example.py",
                "file_content": file_content,
                "cursor_line": 10,
                "cursor_column": 35,
                "repo_dir": None,
                "num_completions": 1,
                "max_tokens": 200
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok") and data.get("primary_completion"):
                completion = data["primary_completion"]
                print("✅ Completion generated successfully")
                print(f"   Length: {len(completion)} characters")
                print(f"   Preview: {completion[:80]}...")
                return True
            else:
                print(f"❌ No completion generated: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_typescript_completion():
    """Test TypeScript completion (like page.tsx)."""
    print("\n=== Test 3: TypeScript Completion ===")
    
    file_content = """export default function ContactPage() {
    return (
        <Section title="Contact">
            <div className="grid gap-4 sm:grid-cols-2">
                {/* Cards */}
            </div>
        </Section>
    );
}

function testFunction() {
    // TODO: add error handling
    """
    
    try:
        response = requests.post(
            f"{SERVER_URL}/completion",
            json={
                "file_path": "page.tsx",
                "file_content": file_content,
                "cursor_line": 11,
                "cursor_column": 1,
                "repo_dir": None,
                "num_completions": 1,
                "max_tokens": 200
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok") and data.get("primary_completion"):
                completion = data["primary_completion"]
                print("✅ TypeScript completion generated")
                print(f"   Length: {len(completion)} characters")
                print(f"   Preview: {completion[:80]}...")
                return True
            else:
                print(f"❌ No completion: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_multiple_completions():
    """Test generating multiple completion candidates."""
    print("\n=== Test 4: Multiple Completions ===")
    
    file_content = """def calculate_total(items):
    # TODO: calculate total
    """
    
    try:
        response = requests.post(
            f"{SERVER_URL}/completion",
            json={
                "file_path": "test.py",
                "file_content": file_content,
                "cursor_line": 2,
                "cursor_column": 25,
                "repo_dir": None,
                "num_completions": 3,
                "max_tokens": 100
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok") and data.get("completions"):
                completions = data["completions"]
                print(f"✅ Generated {len(completions)} completion candidates")
                for i, comp in enumerate(completions, 1):
                    print(f"   {i}. Length: {len(comp)} chars - {comp[:60]}...")
                return True
            else:
                print(f"❌ No completions: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_error_cases():
    """Test error handling."""
    print("\n=== Test 5: Error Handling ===")
    
    test_cases = [
        {
            "name": "Missing file_path",
            "data": {
                "file_content": "test",
                "cursor_line": 1,
                "cursor_column": 1
            },
            "expected_status": 400
        },
        {
            "name": "Missing file_content",
            "data": {
                "file_path": "test.py",
                "cursor_line": 1,
                "cursor_column": 1
            },
            "expected_status": 400
        },
        {
            "name": "Invalid cursor position",
            "data": {
                "file_path": "test.py",
                "file_content": "line1\nline2",
                "cursor_line": 999,
                "cursor_column": 1
            },
            "expected_status": 400
        }
    ]
    
    passed = 0
    for test_case in test_cases:
        try:
            response = requests.post(
                f"{SERVER_URL}/completion",
                json=test_case["data"],
                timeout=10
            )
            
            if response.status_code == test_case["expected_status"]:
                print(f"✅ {test_case['name']}: Correctly returned {response.status_code}")
                passed += 1
            else:
                print(f"❌ {test_case['name']}: Expected {test_case['expected_status']}, got {response.status_code}")
        except Exception as e:
            print(f"❌ {test_case['name']}: Error - {e}")
    
    print(f"\n   Passed: {passed}/{len(test_cases)} error tests")
    return passed == len(test_cases)


def test_performance():
    """Test completion performance (response time)."""
    print("\n=== Test 6: Performance Test ===")
    
    file_content = """def process_data(data):
    # TODO: implement processing
    """
    
    times = []
    for i in range(3):
        try:
            start_time = time.time()
            response = requests.post(
                f"{SERVER_URL}/completion",
                json={
                    "file_path": "test.py",
                    "file_content": file_content,
                    "cursor_line": 2,
                    "cursor_column": 30,
                    "repo_dir": None,
                    "num_completions": 1,
                    "max_tokens": 100
                },
                timeout=30
            )
            end_time = time.time()
            
            if response.status_code == 200:
                elapsed = end_time - start_time
                times.append(elapsed)
                print(f"   Request {i+1}: {elapsed:.2f}s")
            else:
                print(f"   Request {i+1}: Failed (status {response.status_code})")
        except Exception as e:
            print(f"   Request {i+1}: Error - {e}")
    
    if times:
        avg_time = sum(times) / len(times)
        print(f"\n✅ Average response time: {avg_time:.2f}s")
        if avg_time < 5:
            print("   ✅ Performance: Good (<5s)")
        elif avg_time < 10:
            print("   ⚠️  Performance: Acceptable (<10s)")
        else:
            print("   ⚠️  Performance: Slow (>10s)")
        return True
    else:
        print("❌ All requests failed")
        return False


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("AUTOMATED COMPLETION ENDPOINT TEST SUITE")
    print("=" * 60)
    
    results = []
    
    # Test 1: Health check
    results.append(("Health Check", test_health()))
    
    if not results[-1][1]:
        print("\n❌ Server is not running. Start it with: python -m backend.app")
        return
    
    time.sleep(1)  # Brief pause between tests
    
    # Test 2: Basic completion
    results.append(("Basic Completion", test_basic_completion()))
    time.sleep(1)
    
    # Test 3: TypeScript completion
    results.append(("TypeScript Completion", test_typescript_completion()))
    time.sleep(1)
    
    # Test 4: Multiple completions
    results.append(("Multiple Completions", test_multiple_completions()))
    time.sleep(1)
    
    # Test 5: Error handling
    results.append(("Error Handling", test_error_cases()))
    time.sleep(1)
    
    # Test 6: Performance
    results.append(("Performance", test_performance()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Backend is working correctly.")
        print("\n💡 Note: VS Code extension integration still needs manual testing,")
        print("   but the backend endpoint is fully functional!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the errors above.")


if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
