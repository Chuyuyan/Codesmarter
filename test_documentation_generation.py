"""
Test script for the documentation generation endpoint.
"""
import requests
import json

SERVER_URL = "http://127.0.0.1:5050"

def test_generate_docstring():
    """Test generating docstring for a function."""
    print("\n=== Test 1: Generate Docstring ===")
    
    code_snippet = """def calculate_total(items):
    total = 0
    for item in items:
        if 'price' not in item:
            raise ValueError(f"Item missing 'price' key: {item}")
        total += item['price']
    return total"""
    
    response = requests.post(
        f"{SERVER_URL}/generate_docs",
        json={
            "doc_type": "docstring",
            "code_snippet": code_snippet,
            "doc_format": "google",
            "target_name": "calculate_total",
            "repo_dir": "C:\\Users\\57811\\my-portfolio"  # Adjust to your repo
        },
        timeout=180
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get("ok"):
            print("[PASS] Docstring generated successfully!")
            print(f"Format: {data.get('doc_format')}")
            print(f"Language: {data.get('language')}")
            print(f"Target: {data.get('target_name')}")
            print(f"Lines: {data.get('lines')}")
            print(f"\nGenerated Documentation:")
            print("=" * 60)
            print(data.get('documentation', '')[:800])
            if len(data.get('documentation', '')) > 800:
                print(f"\n... (truncated, total {len(data.get('documentation', ''))} chars)")
            print("=" * 60)
            return True
        else:
            print(f"[FAIL] Error: {data.get('error')}")
            return False
    else:
        print(f"[FAIL] HTTP Error: {response.status_code}")
        print(f"Response: {response.text}")
        return False


def test_generate_class_docstring():
    """Test generating docstring for a class."""
    print("\n=== Test 2: Generate Class Docstring ===")
    
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
        return result"""
    
    response = requests.post(
        f"{SERVER_URL}/generate_docs",
        json={
            "doc_type": "docstring",
            "code_snippet": code_snippet,
            "doc_format": "google",
            "target_name": "Calculator",
            "repo_dir": "C:\\Users\\57811\\my-portfolio"
        },
        timeout=180
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get("ok"):
            print("[PASS] Class docstring generated!")
            print(f"Format: {data.get('doc_format')}")
            print(f"Lines: {data.get('lines')}")
            return True
        else:
            print(f"[FAIL] Error: {data.get('error')}")
            return False
    else:
        print(f"[FAIL] HTTP Error: {response.status_code}")
        return False


def test_generate_readme():
    """Test generating README file."""
    print("\n=== Test 3: Generate README ===")
    
    response = requests.post(
        f"{SERVER_URL}/generate_docs",
        json={
            "doc_type": "readme",
            "repo_dir": "C:\\Users\\57811\\my-portfolio",  # Adjust to your repo
            "max_tokens": 4000  # Increased for README
        },
        timeout=300  # Increased timeout for large repositories
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get("ok"):
            print("[PASS] README generated successfully!")
            print(f"Format: {data.get('doc_format')}")
            print(f"Lines: {data.get('lines')}")
            print(f"\nGenerated README Preview:")
            print("=" * 60)
            readme = data.get('documentation', '')
            print(readme[:800])
            if len(readme) > 800:
                print(f"\n... (truncated, total {len(readme)} chars)")
            print("=" * 60)
            return True
        else:
            print(f"[FAIL] Error: {data.get('error')}")
            return False
    else:
        print(f"[FAIL] HTTP Error: {response.status_code}")
        return False


def test_generate_api_docs():
    """Test generating API documentation."""
    print("\n=== Test 4: Generate API Documentation ===")
    
    code_snippet = """@app.route('/api/users', methods=['GET'])
def get_users():
    users = db.get_all_users()
    return jsonify(users)

@app.route('/api/users/<user_id>', methods=['GET'])
def get_user(user_id):
    user = db.get_user(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(user)

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.json
    user = db.create_user(data)
    return jsonify(user), 201"""
    
    response = requests.post(
        f"{SERVER_URL}/generate_docs",
        json={
            "doc_type": "api",
            "code_snippet": code_snippet,
            "doc_format": "markdown",
            "repo_dir": "C:\\Users\\57811\\my-portfolio"
        },
        timeout=180
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get("ok"):
            print("[PASS] API documentation generated!")
            print(f"Format: {data.get('doc_format')}")
            print(f"Lines: {data.get('lines')}")
            return True
        else:
            print(f"[FAIL] Error: {data.get('error')}")
            return False
    else:
        print(f"[FAIL] HTTP Error: {response.status_code}")
        return False


def run_all_tests():
    """Run all documentation generation tests."""
    print("=" * 60)
    print("DOCUMENTATION GENERATION ENDPOINT TEST SUITE")
    print("=" * 60)
    
    results = []
    
    # Test 1: Generate docstring
    try:
        results.append(("Generate Docstring", test_generate_docstring()))
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        results.append(("Generate Docstring", False))
    
    # Test 2: Generate class docstring
    try:
        results.append(("Generate Class Docstring", test_generate_class_docstring()))
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        results.append(("Generate Class Docstring", False))
    
    # Test 3: Generate README
    try:
        results.append(("Generate README", test_generate_readme()))
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        results.append(("Generate README", False))
    
    # Test 4: Generate API docs
    try:
        results.append(("Generate API Documentation", test_generate_api_docs()))
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        results.append(("Generate API Documentation", False))
    
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
        print("\n[SUCCESS] All tests passed! Documentation generation endpoint is working!")
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

