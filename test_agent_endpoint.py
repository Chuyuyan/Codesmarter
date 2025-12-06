"""
Test script for Task 2.5: Integration & Agent Endpoint
Tests the unified /agent endpoint with all agent capabilities.
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

def test_agent_endpoint():
    """Test the /agent endpoint with full agent capabilities."""
    print("=" * 60)
    print("🧪 Test: Unified Agent Endpoint (/agent)")
    print("=" * 60)
    
    complex_question = "How does authentication work in this codebase?"
    
    body = {
        "repo_dir": TEST_REPO,
        "question": complex_question,
        "max_steps": 3,
        "results_per_step": 3,
        "decompose": True
    }
    
    print(f"\n📋 Request:")
    print(f"   Endpoint: POST /agent")
    print(f"   Question: '{complex_question}'")
    print(f"   Repo: {TEST_REPO}")
    print(f"   Max Steps: {body['max_steps']}")
    print(f"   Results per Step: {body['results_per_step']}")
    
    try:
        print(f"\n⏳ Sending request (this may take a while due to multi-step reasoning)...")
        start_time = time.time()
        response = requests.post(f"{SERVER_URL}/agent", json=body, timeout=300)  # 5 min timeout
        elapsed_time = time.time() - start_time
        data = response.json()
        
        if data.get("ok"):
            print(f"\n✅ Success! (took {elapsed_time:.1f} seconds)")
            
            # Check all components
            components_found = []
            
            # 1. Check synthesized answer
            synthesized_answer_data = data.get("synthesized_answer")
            answer = data.get("answer")
            if synthesized_answer_data and synthesized_answer_data.get("synthesized_answer"):
                print(f"\n📝 Synthesized Answer: ✅")
                print(f"   Answer Length: {len(synthesized_answer_data['synthesized_answer'])} chars")
                components_found.append("Answer Synthesis")
            elif answer:
                print(f"\n📝 Answer: ✅")
                print(f"   Answer Length: {len(answer)} chars")
                components_found.append("Answer")
            
            # 2. Check reasoning chain
            reasoning_chain = data.get("reasoning_chain")
            if reasoning_chain:
                print(f"\n🧠 Reasoning Chain: ✅")
                print(f"   Completed Steps: {reasoning_chain.get('completed_steps', 0)}")
                print(f"   Knowledge Entries: {len(reasoning_chain.get('knowledge_entries', []))}")
                print(f"   Key Concepts: {len(reasoning_chain.get('all_key_concepts', []))}")
                print(f"   Discovered Files: {len(reasoning_chain.get('discovered_files', []))}")
                components_found.append("Reasoning Chain")
            
            # 3. Check search steps
            search_steps = data.get("search_steps")
            if search_steps:
                print(f"\n🔍 Search Steps: ✅")
                print(f"   Total Steps: {len(search_steps)}")
                for step in search_steps[:3]:  # Show first 3
                    print(f"   Step {step['step_number']}: {step['query'][:50]}... → {step['results_count']} results")
                components_found.append("Iterative Search")
            
            # 4. Check sub-questions (decomposition)
            sub_questions = data.get("sub_questions")
            if sub_questions and len(sub_questions) > 1:
                print(f"\n❓ Question Decomposition: ✅")
                print(f"   Sub-questions: {len(sub_questions)}")
                for i, sq in enumerate(sub_questions[:3], 1):
                    print(f"     {i}. {sq[:60]}...")
                components_found.append("Question Decomposition")
            
            # 5. Check results
            results = data.get("results")
            if results:
                print(f"\n📊 Results: ✅")
                print(f"   Total Results: {len(results)}")
                print(f"   Unique Files: {data.get('unique_files', 0)}")
                components_found.append("Search Results")
            
            # 6. Check citations
            citations = data.get("citations")
            if citations:
                print(f"\n📚 Citations: ✅")
                print(f"   Citations Count: {len(citations)}")
                components_found.append("Citations")
            
            # Summary
            print(f"\n" + "=" * 60)
            print(f"📋 Components Check:")
            required_components = [
                "Answer Synthesis",
                "Reasoning Chain",
                "Iterative Search",
                "Question Decomposition",
                "Search Results"
            ]
            
            all_present = True
            for comp in required_components:
                status = "✅" if comp in components_found else "❌"
                print(f"   {status} {comp}")
                if comp not in components_found:
                    all_present = False
            
            if all_present:
                print(f"\n🎉 All components working!")
                return True
            else:
                print(f"\n⚠️  Some components missing")
                return False
        else:
            print(f"\n❌ Error: {data.get('error')}")
            return False
    except requests.exceptions.Timeout:
        print(f"\n❌ Request timed out (300s)")
        return False
    except Exception as e:
        print(f"\n❌ Request failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_agent_vs_chat():
    """Compare /agent endpoint with /chat endpoint."""
    print("\n" + "=" * 60)
    print("🧪 Comparison: /agent vs /chat")
    print("=" * 60)
    
    question = "How does authentication work?"
    
    print(f"\n📋 Question: '{question}'")
    print(f"\n/chat endpoint: Single search → Answer")
    print(f"/agent endpoint: Multi-step reasoning → Comprehensive answer")
    
    print(f"\n💡 /agent provides:")
    print(f"   • Question decomposition")
    print(f"   • Iterative search")
    print(f"   • Reasoning chain tracking")
    print(f"   • Comprehensive answer synthesis")
    print(f"   • More thorough exploration")

def main():
    """Run the test."""
    print("=" * 60)
    print("🤖 Testing Unified Agent Endpoint (/agent) - Task 2.5")
    print("=" * 60)

    if not check_server():
        print("❌ Server is not running. Please start the Flask backend server first.")
        print("   Run: python -m backend.app")
        return

    print("🔌 Checking server...")
    print("✅ Server is running")

    success = test_agent_endpoint()
    
    test_agent_vs_chat()

    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    if success:
        print("✅ Test PASSED: Agent endpoint is working correctly!")
        print("\n🎉 Task 2.5: Integration & Agent Endpoint - COMPLETED!")
        print("\n🚀 All Task 2 components integrated:")
        print("   ✅ Task 2.1: Question Decomposition")
        print("   ✅ Task 2.2: Iterative Search Agent")
        print("   ✅ Task 2.3: Reasoning Chain & Context Tracking")
        print("   ✅ Task 2.4: Plan Execution & Answer Synthesis")
        print("   ✅ Task 2.5: Integration & Agent Endpoint")
    else:
        print("❌ Test FAILED: Agent endpoint not working as expected")
    print("=" * 60)

if __name__ == "__main__":
    main()

