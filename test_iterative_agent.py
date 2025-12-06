"""
Test script for iterative search agent functionality.
Tests the /search_iterative endpoint.
"""
import sys
import time
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

def test_iterative_search():
    """Test iterative search with question decomposition."""
    print("=" * 60)
    print("🧪 Test 1: Iterative Search with Question Decomposition")
    print("=" * 60)
    
    question = "How does authentication work in this codebase?"
    
    body = {
        "repo_dir": TEST_REPO,
        "question": question,
        "decompose": True,
        "max_steps": 5,  # Limit to 5 steps for testing
        "results_per_step": 3
    }
    
    print(f"\n📋 Request:")
    print(f"   Question: '{question}'")
    print(f"   Repo: {Path(TEST_REPO).name}")
    print(f"   Max steps: {body['max_steps']}")
    print(f"   Results per step: {body['results_per_step']}")
    
    try:
        print(f"\n⏳ Performing iterative search (this may take a moment)...")
        response = requests.post(
            f"{SERVER_URL}/search_iterative",
            json=body,
            timeout=120
        )
        data = response.json()
        
        if data.get("ok"):
            print(f"\n✅ Iterative search completed!")
            print(f"\n📊 Summary:")
            summary = data.get("summary", {})
            print(f"   Total steps: {summary.get('total_steps', 0)}")
            print(f"   Completed steps: {summary.get('completed_steps', 0)}")
            print(f"   Total results: {data.get('total_results', 0)}")
            print(f"   Unique files: {data.get('unique_files', 0)}")
            
            sub_questions = data.get("sub_questions", [])
            print(f"\n📝 Sub-questions used ({len(sub_questions)}):")
            for i, q in enumerate(sub_questions[:5], 1):  # Show first 5
                print(f"   {i}. {q[:70]}...")
            
            search_steps = data.get("search_steps", [])
            print(f"\n🔍 Search Steps:")
            for step in search_steps:
                print(f"   Step {step['step_number']}: {step['results_count']} results")
                if step.get("files_found"):
                    files_preview = step["files_found"][:2]
                    print(f"      Files: {', '.join(Path(f).name for f in files_preview)}...")
            
            results = data.get("results", [])
            if results:
                print(f"\n📄 Sample Results:")
                for i, result in enumerate(results[:3], 1):  # Show first 3
                    file_name = Path(result.get("file", "")).name
                    query = result.get("search_query", "unknown")
                    print(f"   {i}. {file_name} (from query: '{query[:40]}...')")
                    snippet_preview = result.get("snippet", "")[:80].replace("\n", " ")
                    print(f"      {snippet_preview}...")
            
            return True
        else:
            print(f"\n❌ Error: {data.get('error')}")
            return False
    except Exception as e:
        print(f"\n❌ Request failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_iterative_search_custom_subquestions():
    """Test iterative search with custom sub-questions."""
    print("\n" + "=" * 60)
    print("🧪 Test 2: Iterative Search with Custom Sub-questions")
    print("=" * 60)
    
    sub_questions = [
        "Where are React components defined?",
        "How is state management implemented?",
        "What routing mechanism is used?"
    ]
    
    body = {
        "repo_dir": TEST_REPO,
        "sub_questions": sub_questions,
        "decompose": False,  # Don't decompose, use custom sub-questions
        "results_per_step": 3
    }
    
    print(f"\n📋 Request:")
    print(f"   Custom sub-questions: {len(sub_questions)}")
    for i, q in enumerate(sub_questions, 1):
        print(f"     {i}. {q}")
    
    try:
        print(f"\n⏳ Performing iterative search...")
        response = requests.post(
            f"{SERVER_URL}/search_iterative",
            json=body,
            timeout=90
        )
        data = response.json()
        
        if data.get("ok"):
            print(f"\n✅ Iterative search completed!")
            print(f"   Total results: {data.get('total_results', 0)}")
            print(f"   Unique files: {data.get('unique_files', 0)}")
            
            search_steps = data.get("search_steps", [])
            print(f"\n🔍 Search Steps:")
            for step in search_steps:
                print(f"   Step {step['step_number']}: '{step['query'][:50]}...' → {step['results_count']} results")
            
            return True
        else:
            print(f"\n❌ Error: {data.get('error')}")
            return False
    except Exception as e:
        print(f"\n❌ Request failed: {e}")
        return False

def main():
    """Run all iterative agent tests."""
    print("=" * 60)
    print("🔧 Testing Iterative Search Agent")
    print("=" * 60)
    
    # Check server
    print("\n🔌 Checking server...")
    if not check_server():
        print(f"❌ Server not running at {SERVER_URL}")
        print("   Please start the server: python -m backend.app")
        return False
    print("✅ Server is running")
    
    # Check if repo exists
    if not Path(TEST_REPO).exists():
        print(f"\n⚠️  Test repository not found: {TEST_REPO}")
        print("   Please update TEST_REPO in the script")
        return False
    
    # Run tests
    results = []
    
    results.append(("Iterative Search with Decomposition", test_iterative_search()))
    results.append(("Iterative Search with Custom Sub-questions", test_iterative_search_custom_subquestions()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"   {name}: {status}")
    
    all_passed = all(success for _, success in results)
    
    if all_passed:
        print("\n🎉 All tests passed! Iterative search agent is working.")
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

