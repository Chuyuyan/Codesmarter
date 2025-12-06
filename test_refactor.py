"""
Test script for the /refactor endpoint.
Demonstrates three ways to use the refactoring endpoint:
1. Search query to find code
2. Specific file path
3. Direct code snippets
"""
import sys
import json
import requests
from pathlib import Path

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

SERVER_URL = "http://127.0.0.1:5050"
TEST_REPO = r"C:\Users\57811\my-portfolio"

def check_server():
    """Check if server is running."""
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def test_refactor_by_query():
    """Test refactoring using a search query."""
    print("=" * 60)
    print("🧪 Test 1: Refactor using search query")
    print("=" * 60)
    
    body = {
        "repo_dir": TEST_REPO,
        "query": "function component",
        "focus": "readability",
        "top_k": 3
    }
    
    print(f"\n📋 Request:")
    print(f"   Query: '{body['query']}'")
    print(f"   Focus: {body['focus']}")
    print(f"   Top K: {body['top_k']}")
    
    try:
        response = requests.post(
            f"{SERVER_URL}/refactor",
            json=body,
            timeout=120  # Increased timeout for LLM processing
        )
        data = response.json()
        
        if data.get("ok"):
            print(f"\n✅ Success! Found {data.get('count', 0)} code snippet(s)")
            print(f"\n📝 Refactoring Suggestions:")
            print("-" * 60)
            print(data.get("refactoring_suggestions", ""))
            print("-" * 60)
            return True
        else:
            print(f"\n❌ Error: {data.get('error')}")
            return False
    except Exception as e:
        print(f"\n❌ Request failed: {e}")
        return False

def test_refactor_by_file():
    """Test refactoring a specific file."""
    print("\n" + "=" * 60)
    print("🧪 Test 2: Refactor specific file")
    print("=" * 60)
    
    # Try to find a Python or JavaScript file in the repo
    repo_path = Path(TEST_REPO)
    test_files = list(repo_path.rglob("*.py")) + list(repo_path.rglob("*.js")) + list(repo_path.rglob("*.ts"))
    
    if not test_files:
        print("\n⚠️  No Python/JS/TS files found in repository")
        print("   Skipping file-based test")
        return True
    
    test_file = test_files[0]
    relative_path = test_file.relative_to(repo_path)
    
    body = {
        "repo_dir": TEST_REPO,
        "file_path": str(relative_path),
        "focus": "maintainability"
    }
    
    print(f"\n📋 Request:")
    print(f"   File: {relative_path}")
    print(f"   Focus: {body['focus']}")
    
    try:
        response = requests.post(
            f"{SERVER_URL}/refactor",
            json=body,
            timeout=120  # Increased timeout for LLM processing
        )
        data = response.json()
        
        if data.get("ok"):
            print(f"\n✅ Success! Analyzed file")
            print(f"\n📝 Refactoring Suggestions:")
            print("-" * 60)
            # Show first 500 chars of suggestions
            suggestions = data.get("refactoring_suggestions", "")
            print(suggestions[:500] + "..." if len(suggestions) > 500 else suggestions)
            print("-" * 60)
            return True
        else:
            print(f"\n❌ Error: {data.get('error')}")
            return False
    except Exception as e:
        print(f"\n❌ Request failed: {e}")
        return False

def test_refactor_by_snippets():
    """Test refactoring using direct code snippets."""
    print("\n" + "=" * 60)
    print("🧪 Test 3: Refactor direct code snippets")
    print("=" * 60)
    
    # Example code snippet to refactor
    example_code = """
def process_data(items):
    result = []
    for i in range(len(items)):
        item = items[i]
        if item > 0:
            result.append(item * 2)
        else:
            result.append(0)
    return result
"""
    
    body = {
        "code_snippets": [{
            "file": "example.py",
            "start": 1,
            "end": 10,
            "snippet": example_code.strip()
        }],
        "focus": "readability and pythonic style"
    }
    
    print(f"\n📋 Request:")
    print(f"   Code snippet provided directly")
    print(f"   Focus: {body['focus']}")
    print(f"\n📄 Code to refactor:")
    print(example_code)
    
    try:
        response = requests.post(
            f"{SERVER_URL}/refactor",
            json=body,
            timeout=120  # Increased timeout for LLM processing
        )
        data = response.json()
        
        if data.get("ok"):
            print(f"\n✅ Success!")
            print(f"\n📝 Refactoring Suggestions:")
            print("-" * 60)
            print(data.get("refactoring_suggestions", ""))
            print("-" * 60)
            return True
        else:
            print(f"\n❌ Error: {data.get('error')}")
            return False
    except Exception as e:
        print(f"\n❌ Request failed: {e}")
        return False

def main():
    """Run all refactoring tests."""
    print("=" * 60)
    print("🔧 Testing Refactoring Endpoint (/refactor)")
    print("=" * 60)
    
    # Check server
    print("\n🔌 Checking server...")
    if not check_server():
        print(f"❌ Server not running at {SERVER_URL}")
        print("   Please start the server: python -m backend.app")
        return False
    print("✅ Server is running")
    
    # Run tests
    results = []
    
    # Test 1: Query-based
    results.append(("Query-based", test_refactor_by_query()))
    
    # Test 2: File-based
    results.append(("File-based", test_refactor_by_file()))
    
    # Test 3: Snippet-based
    results.append(("Snippet-based", test_refactor_by_snippets()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"   {name}: {status}")
    
    all_passed = all(success for _, success in results)
    
    if all_passed:
        print("\n🎉 All tests passed! Refactoring endpoint is working.")
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
    
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted")
        sys.exit(1)

