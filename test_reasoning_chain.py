"""
Test script for Task 2.3: Reasoning Chain & Context Tracking
Tests that the reasoning chain tracks knowledge across search steps.
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

def test_reasoning_chain():
    """Test that reasoning chain is included in iterative search results."""
    print("=" * 60)
    print("🧪 Test: Reasoning Chain & Context Tracking")
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
        response = requests.post(f"{SERVER_URL}/search_iterative", json=body, timeout=180)
        data = response.json()
        
        if data.get("ok"):
            print(f"\n✅ Success!")
            print(f"   Total Results: {data.get('total_results', 0)}")
            print(f"   Unique Files: {data.get('unique_files', 0)}")
            
            # Check for reasoning chain data
            reasoning_chain = data.get("reasoning_chain")
            reasoning_summary = data.get("reasoning_summary")
            
            if reasoning_chain:
                print(f"\n📊 Reasoning Chain Found!")
                print(f"   Completed Steps: {reasoning_chain.get('completed_steps', 0)}")
                print(f"   Knowledge Entries: {len(reasoning_chain.get('knowledge_entries', []))}")
                print(f"   Key Concepts: {len(reasoning_chain.get('all_key_concepts', []))}")
                print(f"   Discovered Files: {len(reasoning_chain.get('discovered_files', []))}")
                print(f"   Discovered Functions: {len(reasoning_chain.get('discovered_functions', []))}")
                print(f"   Discovered Classes: {len(reasoning_chain.get('discovered_classes', []))}")
                
                # Show knowledge entries
                knowledge_entries = reasoning_chain.get('knowledge_entries', [])
                if knowledge_entries:
                    print(f"\n📝 Knowledge Entries:")
                    for entry in knowledge_entries[:3]:  # Show first 3
                        print(f"   Step {entry.get('step_number')}: {entry.get('query', '')[:60]}...")
                        print(f"      Findings: {entry.get('findings', '')[:80]}...")
                        if entry.get('key_concepts'):
                            print(f"      Concepts: {', '.join(entry.get('key_concepts', [])[:5])}")
                
                if reasoning_summary:
                    print(f"\n📋 Reasoning Summary (first 400 chars):")
                    print(f"   {reasoning_summary[:400]}...")
                
                return True
            else:
                print(f"\n❌ Reasoning chain not found in response!")
                return False
        else:
            print(f"\n❌ Error: {data.get('error')}")
            return False
    except requests.exceptions.Timeout:
        print(f"\n❌ Request timed out")
        return False
    except Exception as e:
        print(f"\n❌ Request failed: {e}")
        return False

def main():
    """Run the test."""
    print("=" * 60)
    print("🧠 Testing Reasoning Chain & Context Tracking (Task 2.3)")
    print("=" * 60)

    if not check_server():
        print("❌ Server is not running. Please start the Flask backend server first.")
        print("   Run: python -m backend.app")
        return

    print("🔌 Checking server...")
    print("✅ Server is running")

    success = test_reasoning_chain()

    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    if success:
        print("✅ Test PASSED: Reasoning chain is working correctly!")
        print("\n🎉 Task 2.3: Reasoning Chain & Context Tracking - COMPLETED!")
    else:
        print("❌ Test FAILED: Reasoning chain not working as expected")
    print("=" * 60)

if __name__ == "__main__":
    main()

