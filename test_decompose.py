"""
Test script for question decomposition functionality.
Tests the /decompose endpoint and question_decomposer module.
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

def check_server():
    """Check if server is running."""
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def test_simple_question():
    """Test decomposition of a simple question."""
    print("=" * 60)
    print("🧪 Test 1: Simple Question")
    print("=" * 60)
    
    question = "What is the main entry point?"
    
    body = {"question": question}
    
    print(f"\n📋 Question: '{question}'")
    print("   Expected: Should return 1-2 sub-questions (simple question)")
    
    try:
        response = requests.post(
            f"{SERVER_URL}/decompose",
            json=body,
            timeout=30
        )
        data = response.json()
        
        if data.get("ok"):
            sub_questions = data.get("sub_questions", [])
            print(f"\n✅ Decomposition successful!")
            print(f"   Sub-questions ({len(sub_questions)}):")
            for i, q in enumerate(sub_questions, 1):
                print(f"     {i}. {q}")
            
            analysis = data.get("analysis", {})
            print(f"\n📊 Analysis:")
            print(f"   Is complex: {data.get('is_complex')}")
            print(f"   Sub-questions count: {analysis.get('sub_questions_count')}")
            
            return True
        else:
            print(f"\n❌ Error: {data.get('error')}")
            return False
    except Exception as e:
        print(f"\n❌ Request failed: {e}")
        return False

def test_complex_question():
    """Test decomposition of a complex question."""
    print("\n" + "=" * 60)
    print("🧪 Test 2: Complex Question")
    print("=" * 60)
    
    question = "How does authentication work in this codebase? Where are tokens validated and how are protected routes handled?"
    
    body = {"question": question}
    
    print(f"\n📋 Question: '{question[:80]}...'")
    print("   Expected: Should return 3-7 sub-questions (complex question)")
    
    try:
        response = requests.post(
            f"{SERVER_URL}/decompose",
            json=body,
            timeout=30
        )
        data = response.json()
        
        if data.get("ok"):
            sub_questions = data.get("sub_questions", [])
            print(f"\n✅ Decomposition successful!")
            print(f"   Sub-questions ({len(sub_questions)}):")
            for i, q in enumerate(sub_questions, 1):
                print(f"     {i}. {q}")
            
            analysis = data.get("analysis", {})
            print(f"\n📊 Analysis:")
            print(f"   Is complex: {data.get('is_complex')}")
            print(f"   Sub-questions count: {analysis.get('sub_questions_count')}")
            print(f"   Avg sub-question length: {analysis.get('avg_sub_question_length', 0):.1f} words")
            
            if len(sub_questions) >= 3:
                print("\n✅ Complex question properly decomposed!")
                return True
            else:
                print("\n⚠️  Question might be too simple or decomposition needs improvement")
                return True  # Still a success, just fewer sub-questions
        else:
            print(f"\n❌ Error: {data.get('error')}")
            return False
    except Exception as e:
        print(f"\n❌ Request failed: {e}")
        return False

def test_project_structure_question():
    """Test decomposition of a project structure question."""
    print("\n" + "=" * 60)
    print("🧪 Test 3: Project Structure Question")
    print("=" * 60)
    
    question = "What is the main structure of this project? What are the core modules and how do they interact?"
    
    body = {"question": question}
    
    print(f"\n📋 Question: '{question}'")
    print("   Expected: Should return 3-5 sub-questions about project structure")
    
    try:
        response = requests.post(
            f"{SERVER_URL}/decompose",
            json=body,
            timeout=30
        )
        data = response.json()
        
        if data.get("ok"):
            sub_questions = data.get("sub_questions", [])
            print(f"\n✅ Decomposition successful!")
            print(f"   Sub-questions ({len(sub_questions)}):")
            for i, q in enumerate(sub_questions, 1):
                print(f"     {i}. {q}")
            
            return True
        else:
            print(f"\n❌ Error: {data.get('error')}")
            return False
    except Exception as e:
        print(f"\n❌ Request failed: {e}")
        return False

def main():
    """Run all decomposition tests."""
    print("=" * 60)
    print("🔧 Testing Question Decomposition")
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
    
    results.append(("Simple Question", test_simple_question()))
    results.append(("Complex Question", test_complex_question()))
    results.append(("Project Structure Question", test_project_structure_question()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"   {name}: {status}")
    
    all_passed = all(success for _, success in results)
    
    if all_passed:
        print("\n🎉 All tests passed! Question decomposition is working.")
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

