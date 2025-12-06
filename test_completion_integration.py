"""
Comprehensive automated tests for inline code completion feature.
Tests both backend endpoint and simulates VS Code extension integration.
"""
import requests
import json
import time
from pathlib import Path

SERVER_URL = "http://127.0.0.1:5050"

def test_backend_health():
    """Test if backend server is running."""
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        print("✅ Backend server is running")
        return True
    except Exception as e:
        print(f"❌ Backend server not accessible: {e}")
        return False

def test_completion_endpoint_basic():
    """Test basic completion endpoint functionality."""
    print("\n=== Test 1: Basic Completion Endpoint ===")
    
    file_content = """def calculate_total(items):
    total = 0
    for item in items:
        total += item['price']
    return total

def process_order(order):
    # TODO: implement order processing
    """
    
    response = requests.post(
        f"{SERVER_URL}/completion",
        json={
            "file_path": "test_example.py",
            "file_content": file_content,
            "cursor_line": 10,
            "cursor_column": 35,
            "num_completions": 1,
            "max_tokens": 200
        },
        timeout=30
    )
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data.get("ok") == True, f"Expected ok=True, got {data}"
    
    completion = data.get("primary_completion", "")
    assert len(completion) > 0, "Completion should not be empty"
    
    print(f"✅ Completion generated: {len(completion)} characters")
    print(f"   Preview: {completion[:80]}...")
    return True

def test_completion_typescript():
    """Test completion for TypeScript/React code."""
    print("\n=== Test 2: TypeScript Completion ===")
    
    file_content = """export default function ContactPage() {
    return (
        <Section title="Contact">
            <div className="grid gap-4 sm:grid-cols-2">
                <Card title="Email" desc={CONTACT.email} href={`mailto:${CONTACT.email}`} />
                <Card title="Phone" desc={CONTACT.phone} href={`tel:${CONTACT.phone}`} />
            </div>
        </Section>
    );
}

function handleSubmit() {
    // TODO: add error handling
    """
    
    response = requests.post(
        f"{SERVER_URL}/completion",
        json={
            "file_path": "app/contact/page.tsx",
            "file_content": file_content,
            "cursor_line": 12,
            "cursor_column": 32,  # After "// TODO: add error handling"
            "num_completions": 1,
            "max_tokens": 200
        },
        timeout=30
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data.get("ok") == True
    
    completion = data.get("primary_completion", "")
    assert len(completion) > 0
    
    print(f"✅ TypeScript completion generated: {len(completion)} characters")
    print(f"   Preview: {completion[:80]}...")
    return True

def test_completion_with_repo_context():
    """Test completion with repository context (requires indexed repo)."""
    print("\n=== Test 3: Completion with Repo Context ===")
    
    # You need to provide a real repo path for this test
    repo_dir = "C:\\Users\\57811\\my-portfolio"  # Update with your repo path
    
    if not Path(repo_dir).exists():
        print(f"⚠️  Skipping: Repository not found at {repo_dir}")
        return True  # Skip test if repo doesn't exist
    
    file_content = """function testFunction() {
    // TODO: implement
    """
    
    response = requests.post(
        f"{SERVER_URL}/completion",
        json={
            "file_path": f"{repo_dir}/test.py",
            "file_content": file_content,
            "cursor_line": 2,
            "cursor_column": 20,
            "repo_dir": repo_dir,  # Include repo context
            "num_completions": 1,
            "max_tokens": 200
        },
        timeout=30
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data.get("ok") == True
    
    completion = data.get("primary_completion", "")
    assert len(completion) > 0
    
    print(f"✅ Completion with repo context generated: {len(completion)} characters")
    return True

def test_completion_multiple_candidates():
    """Test generating multiple completion candidates."""
    print("\n=== Test 4: Multiple Completion Candidates ===")
    
    file_content = """def process_data(data):
    # TODO: implement processing
    """
    
    response = requests.post(
        f"{SERVER_URL}/completion",
        json={
            "file_path": "test.py",
            "file_content": file_content,
            "cursor_line": 2,
            "cursor_column": 30,
            "num_completions": 3,
            "max_tokens": 150
        },
        timeout=45
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data.get("ok") == True
    
    completions = data.get("completions", [])
    assert len(completions) > 0, "Should return at least one completion"
    
    print(f"✅ Generated {len(completions)} completion candidates")
    for i, comp in enumerate(completions[:3], 1):
        print(f"   Candidate {i}: {len(comp)} chars")
    return True

def test_completion_edge_cases():
    """Test edge cases and error handling."""
    print("\n=== Test 5: Edge Cases ===")
    
    # Test 1: Empty file
    response = requests.post(
        f"{SERVER_URL}/completion",
        json={
            "file_path": "empty.py",
            "file_content": "",
            "cursor_line": 1,
            "cursor_column": 1,
        },
        timeout=30
    )
    assert response.status_code == 200  # Should handle gracefully
    
    # Test 2: Invalid cursor position
    response = requests.post(
        f"{SERVER_URL}/completion",
        json={
            "file_path": "test.py",
            "file_content": "def test():\n    pass",
            "cursor_line": 100,  # Out of range
            "cursor_column": 1,
        },
        timeout=30
    )
    assert response.status_code == 400  # Should return error
    
    # Test 3: Missing required fields
    response = requests.post(
        f"{SERVER_URL}/completion",
        json={
            "file_path": "test.py",
            # Missing file_content, cursor_line, cursor_column
        },
        timeout=30
    )
    assert response.status_code == 400  # Should return error
    
    print("✅ Edge cases handled correctly")
    return True

def test_completion_performance():
    """Test completion performance (response time)."""
    print("\n=== Test 6: Performance Test ===")
    
    file_content = """def example_function():
    # TODO: add implementation
    """
    
    start_time = time.time()
    response = requests.post(
        f"{SERVER_URL}/completion",
        json={
            "file_path": "test.py",
            "file_content": file_content,
            "cursor_line": 2,
            "cursor_column": 30,
            "num_completions": 1,
            "max_tokens": 200
        },
        timeout=30
    )
    elapsed_time = time.time() - start_time
    
    assert response.status_code == 200
    data = response.json()
    assert data.get("ok") == True
    
    print(f"✅ Completion generated in {elapsed_time:.2f} seconds")
    
    if elapsed_time < 5:
        print("   ⚡ Fast response (< 5s)")
    elif elapsed_time < 10:
        print("   ✅ Acceptable response (< 10s)")
    else:
        print("   ⚠️  Slow response (> 10s)")
    
    return True

def simulate_vscode_extension_call():
    """Simulate what VS Code extension would do."""
    print("\n=== Test 7: Simulate VS Code Extension ===")
    
    # This simulates the exact call the extension would make
    file_content = """export default function ContactPage() {
    return (
        <Section title="Contact">
            <div className="grid gap-4 sm:grid-cols-2">
                <Card title="Email" desc={CONTACT.email} href={`mailto:${CONTACT.email}`} />
            </div>
        </Section>
    );
}

function handleSubmit() {
    // TODO: add error handling
    """
    
    # Simulate VS Code position (VS Code uses 0-indexed, we convert to 1-indexed)
    vscode_line = 11  # 0-indexed
    vscode_column = 32  # 0-indexed
    
    # Convert to backend format (1-indexed)
    cursor_line = vscode_line + 1
    cursor_column = vscode_column + 1
    
    response = requests.post(
        f"{SERVER_URL}/completion",
        json={
            "file_path": "app/contact/page.tsx",
            "file_content": file_content,
            "cursor_line": cursor_line,
            "cursor_column": cursor_column,
            "repo_dir": None,  # Extension would provide this if workspace is open
            "num_completions": 1,
            "max_tokens": 200
        },
        timeout=30
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data.get("ok") == True
    
    completion = data.get("primary_completion", "")
    assert len(completion) > 0
    
    print(f"✅ Simulated VS Code extension call successful")
    print(f"   VS Code position: Line {vscode_line}, Column {vscode_column}")
    print(f"   Backend position: Line {cursor_line}, Column {cursor_column}")
    print(f"   Completion: {len(completion)} characters")
    
    return True

def run_all_tests():
    """Run all completion tests."""
    print("=" * 60)
    print("Automated Completion Tests")
    print("=" * 60)
    
    # Check backend first
    if not test_backend_health():
        print("\n❌ Backend server is not running!")
        print("   Start it with: python -m backend.app")
        return False
    
    tests = [
        ("Basic Completion", test_completion_endpoint_basic),
        ("TypeScript Completion", test_completion_typescript),
        ("Completion with Repo Context", test_completion_with_repo_context),
        ("Multiple Candidates", test_completion_multiple_candidates),
        ("Edge Cases", test_completion_edge_cases),
        ("Performance", test_completion_performance),
        ("Simulate VS Code Extension", simulate_vscode_extension_call),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            results.append((test_name, False))
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)

