"""
Test script for the code generation endpoint.
"""
import requests
import json

SERVER_URL = "http://127.0.0.1:5050"

def test_generate_function():
    """Test generating a function."""
    print("\n=== Test 1: Generate Function ===")
    
    response = requests.post(
        f"{SERVER_URL}/generate",
        json={
            "request": "Generate a function to calculate the factorial of a number",
            "generation_type": "function",
            "language": "python",
            "max_tokens": 500
        },
        timeout=60
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get("ok"):
            print("✅ Function generated successfully!")
            print(f"Language: {data.get('language')}")
            print(f"Type: {data.get('generation_type')}")
            print(f"Syntax Valid: {data.get('syntax_valid')}")
            print(f"Length: {data.get('length')} characters")
            print(f"Lines: {data.get('lines')}")
            print("\nGenerated Code:")
            print("=" * 60)
            print(data.get("generated_code"))
            print("=" * 60)
            return True
        else:
            print(f"❌ Error: {data.get('error')}")
            return False
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        print(f"Response: {response.text}")
        return False


def test_generate_class():
    """Test generating a class."""
    print("\n=== Test 2: Generate Class ===")
    
    response = requests.post(
        f"{SERVER_URL}/generate",
        json={
            "request": "Generate a User class with name, email, and age properties, and a method to get user info",
            "generation_type": "class",
            "language": "python",
            "max_tokens": 500
        },
        timeout=60
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get("ok"):
            print("✅ Class generated successfully!")
            print(f"Language: {data.get('language')}")
            print(f"Syntax Valid: {data.get('syntax_valid')}")
            print(f"Length: {data.get('length')} characters")
            print("\nGenerated Code:")
            print("=" * 60)
            print(data.get("generated_code"))
            print("=" * 60)
            return True
        else:
            print(f"❌ Error: {data.get('error')}")
            return False
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        return False


def test_generate_with_context():
    """Test generating code with codebase context."""
    print("\n=== Test 3: Generate with Codebase Context ===")
    
    response = requests.post(
        f"{SERVER_URL}/generate",
        json={
            "request": "Generate a function to validate email addresses",
            "generation_type": "function",
            "language": "python",
            "target_file": "utils.py",
            "repo_dir": "C:\\Users\\57811\\my-portfolio",  # Adjust to your repo
            "max_tokens": 500
        },
        timeout=60
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get("ok"):
            print("✅ Code generated with context!")
            print(f"Syntax Valid: {data.get('syntax_valid')}")
            print("\nGenerated Code:")
            print("=" * 60)
            print(data.get("generated_code")[:300] + "..." if len(data.get("generated_code", "")) > 300 else data.get("generated_code"))
            print("=" * 60)
            return True
        else:
            print(f"❌ Error: {data.get('error')}")
            return False
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        return False


def test_generate_test():
    """Test generating unit tests."""
    print("\n=== Test 4: Generate Unit Tests ===")
    
    code_to_test = """def calculate_total(items):
    total = 0
    for item in items:
        total += item.get('price', 0)
    return total"""
    
    response = requests.post(
        f"{SERVER_URL}/generate",
        json={
            "request": "Generate unit tests for this function",
            "generation_type": "test",
            "language": "python",
            "code_to_test": code_to_test,
            "max_tokens": 1000
        },
        timeout=60
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get("ok"):
            print("✅ Tests generated successfully!")
            print(f"Language: {data.get('language')}")
            print(f"Length: {data.get('length')} characters")
            print("\nGenerated Tests:")
            print("=" * 60)
            print(data.get("generated_code"))
            print("=" * 60)
            return True
        else:
            print(f"❌ Error: {data.get('error')}")
            return False
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        return False


def run_all_tests():
    """Run all generation tests."""
    print("=" * 60)
    print("CODE GENERATION ENDPOINT TEST SUITE")
    print("=" * 60)
    
    results = []
    
    # Test 1: Generate function
    results.append(("Generate Function", test_generate_function()))
    
    # Test 2: Generate class
    results.append(("Generate Class", test_generate_class()))
    
    # Test 3: Generate with context (optional - might fail if repo not indexed)
    try:
        results.append(("Generate with Context", test_generate_with_context()))
    except:
        results.append(("Generate with Context", False))
    
    # Test 4: Generate tests
    results.append(("Generate Tests", test_generate_test()))
    
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
        print("\n🎉 All tests passed! Code generation is working!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")


if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

