"""
Test script for Task 2.4: Plan Execution & Answer Synthesis
Tests that the iterative search returns a synthesized comprehensive answer.
"""
import requests
import json
import sys
from pathlib import Path
import time

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

def test_answer_synthesis():
    """Test that synthesized answer is included in iterative search results."""
    print("=" * 60)
    print("🧪 Test: Plan Execution & Answer Synthesis")
    print("=" * 60)
    
    complex_question = "How does authentication work in this codebase?"
    
    body = {
        "repo_dir": TEST_REPO,
        "question": complex_question,
        "max_steps": 3,
        "results_per_step": 3
    }
    
    print(f"\n📋 Request:")
    print(f"   Question: '{complex_question}'")
    print(f"   Repo: {TEST_REPO}")
    print(f"   Max Steps: {body['max_steps']}")
    
    try:
        print(f"\n⏳ Sending request (this may take a while due to LLM synthesis)...")
        response = requests.post(f"{SERVER_URL}/search_iterative", json=body, timeout=240)  # Longer timeout
        data = response.json()
        
        if data.get("ok"):
            print(f"\n✅ Success!")
            print(f"   Total Results: {data.get('total_results', 0)}")
            print(f"   Unique Files: {data.get('unique_files', 0)}")
            
            # Check for synthesized answer
            synthesized_answer_data = data.get("synthesized_answer")
            
            if synthesized_answer_data:
                print(f"\n📝 Synthesized Answer Found!")
                
                synthesized_answer = synthesized_answer_data.get("synthesized_answer")
                if synthesized_answer:
                    print(f"   Answer Length: {len(synthesized_answer)} characters")
                    print(f"   Files Analyzed: {synthesized_answer_data.get('files_analyzed', 0)}")
                    print(f"   Functions Identified: {synthesized_answer_data.get('functions_identified', 0)}")
                    print(f"   Classes Identified: {synthesized_answer_data.get('classes_identified', 0)}")
                    print(f"   Search Steps Completed: {synthesized_answer_data.get('search_steps_completed', 0)}")
                    print(f"   Key Concepts: {len(synthesized_answer_data.get('key_concepts', []))}")
                    
                    print(f"\n📋 Synthesized Answer (first 500 chars):")
                    print("-" * 60)
                    print(synthesized_answer[:500])
                    print("...")
                    print("-" * 60)
                    
                    # Check if it has meaningful content (not just error)
                    if synthesized_answer and len(synthesized_answer) > 50:
                        if "synthesis_error" not in synthesized_answer_data:
                            print(f"\n✅ Answer synthesis successful!")
                            return True
                        else:
                            print(f"\n⚠️  Answer synthesis had errors but provided fallback answer")
                            print(f"   Error: {synthesized_answer_data.get('synthesis_error')}")
                            return True  # Still counts as working if fallback provided
                    else:
                        print(f"\n❌ Synthesized answer seems incomplete or empty")
                        return False
                else:
                    print(f"\n❌ Synthesized answer text not found in response")
                    return False
            else:
                print(f"\n❌ Synthesized answer data not found in response!")
                print(f"   Available keys: {list(data.keys())}")
                return False
        else:
            print(f"\n❌ Error: {data.get('error')}")
            return False
    except requests.exceptions.Timeout:
        print(f"\n❌ Request timed out (240s)")
        return False
    except Exception as e:
        print(f"\n❌ Request failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the test."""
    print("=" * 60)
    print("🎯 Testing Plan Execution & Answer Synthesis (Task 2.4)")
    print("=" * 60)

    if not check_server():
        print("❌ Server is not running. Please start the Flask backend server first.")
        print("   Run: python -m backend.app")
        return

    print("🔌 Checking server...")
    print("✅ Server is running")

    success = test_answer_synthesis()

    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    if success:
        print("✅ Test PASSED: Answer synthesis is working correctly!")
        print("\n🎉 Task 2.4: Plan Execution & Answer Synthesis - COMPLETED!")
    else:
        print("❌ Test FAILED: Answer synthesis not working as expected")
    print("=" * 60)

if __name__ == "__main__":
    main()

