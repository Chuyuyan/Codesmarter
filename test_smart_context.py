"""
Test script for Better Context Window Management.
Tests smart context prioritization, filtering, and integration.
"""
import requests
import json
import sys
from pathlib import Path

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

SERVER_URL = "http://127.0.0.1:5050"
TEST_REPO = r"C:\Users\57811\my-portfolio"  # Update with your repo path

def test_server_health():
    """Test if server is running."""
    print("\n=== Test 0: Server Health Check ===")
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=5)
        if response.status_code == 200:
            print("[PASS] Server is running!")
            return True
        else:
            print(f"[FAIL] Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("[FAIL] Cannot connect to server. Make sure it's running at http://127.0.0.1:5050")
        print("  Start server with: python -m backend.app")
        return False
    except Exception as e:
        print(f"[FAIL] Exception: {e}")
        return False


def test_chat_with_smart_context():
    """Test /chat endpoint with smart context prioritization."""
    print("\n=== Test 1: Chat with Smart Context Prioritization ===")
    
    try:
        response = requests.post(
            f"{SERVER_URL}/chat",
            json={
                "repo_dir": TEST_REPO,
                "question": "How does authentication work?",
                "analysis_type": "explain"
            },
            timeout=120
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                print("[PASS] Chat endpoint works with smart context!")
                print(f"  Answer length: {len(data.get('answer', ''))} chars")
                print(f"  Citations: {len(data.get('citations', []))} files")
                
                # Check if answer is relevant (mentions authentication-related terms)
                answer = data.get('answer', '').lower()
                relevant_terms = ['auth', 'login', 'password', 'token', 'session', 'user']
                found_terms = [term for term in relevant_terms if term in answer]
                
                if found_terms:
                    print(f"  [PASS] Answer contains relevant terms: {', '.join(found_terms)}")
                else:
                    print(f"  [INFO] Answer may not contain expected authentication terms")
                
                return True
            else:
                print(f"[FAIL] Error: {data.get('error')}")
                return False
        else:
            print(f"[FAIL] HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print("[FAIL] Request timed out after 120 seconds")
        return False
    except Exception as e:
        print(f"[FAIL] Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_refactor_with_file_priority():
    """Test /refactor endpoint with file_path priority."""
    print("\n=== Test 2: Refactor with File Path Priority ===")
    
    # First, find a Python file in the repo
    repo_path = Path(TEST_REPO)
    python_files = list(repo_path.rglob("*.py"))
    
    if not python_files:
        print("[SKIP] No Python files found in repository")
        return True
    
    test_file = python_files[0]
    print(f"  Testing with file: {test_file.name}")
    
    try:
        response = requests.post(
            f"{SERVER_URL}/refactor",
            json={
                "file_path": str(test_file),
                "repo_dir": TEST_REPO,
                "top_k": 2,
                "focus": "readability"
            },
            timeout=180
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                print("[PASS] Refactor endpoint works with smart context!")
                print(f"  Suggestions length: {len(data.get('refactoring_suggestions', ''))} chars")
                print(f"  Format: {data.get('format')}")
                print(f"  Focus: {data.get('focus')}")
                
                # Check if suggestions mention the target file
                suggestions = data.get('refactoring_suggestions', '')
                if test_file.name.lower() in suggestions.lower():
                    print(f"  [PASS] Suggestions reference target file: {test_file.name}")
                else:
                    print(f"  [INFO] Suggestions may not explicitly mention file name")
                
                return True
            else:
                print(f"[FAIL] Error: {data.get('error')}")
                return False
        else:
            print(f"[FAIL] HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print("[FAIL] Request timed out after 180 seconds")
        return False
    except Exception as e:
        print(f"[FAIL] Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_smart_context_module():
    """Test smart context module directly."""
    print("\n=== Test 3: Smart Context Module Direct Test ===")
    
    try:
        from backend.modules.smart_context import (
            prioritize_context,
            filter_irrelevant_code,
            calculate_relevance_score,
            detect_language
        )
        
        print("[PASS] Smart context module imports successfully!")
        
        # Test language detection
        test_cases = [
            ("test.py", "python"),
            ("test.js", "javascript"),
            ("test.ts", "typescript"),
            ("test.java", "java"),
        ]
        
        all_passed = True
        for file_path, expected_lang in test_cases:
            detected = detect_language(file_path)
            if detected == expected_lang:
                print(f"  [PASS] Language detection: {file_path} -> {detected}")
            else:
                print(f"  [FAIL] Language detection: {file_path} -> {detected} (expected {expected_lang})")
                all_passed = False
        
        # Test filtering irrelevant code
        test_code = """
# This is a comment
import os
import sys
from typing import List

def important_function():
    return "This is important"
"""
        filtered = filter_irrelevant_code(test_code, "test.py")
        if "important_function" in filtered:
            print("  [PASS] Filtering preserves important code")
        else:
            print("  [FAIL] Filtering removed important code")
            all_passed = False
        
        # Test relevance scoring
        evidence = {
            "file": "test.py",
            "snippet": "def authenticate_user(username, password): return True",
            "start": 1,
            "end": 1
        }
        score = calculate_relevance_score(evidence, query="authentication")
        if score > 1.0:  # Should have boosted score
            print(f"  [PASS] Relevance scoring works (score: {score:.2f})")
        else:
            print(f"  [FAIL] Relevance scoring may not be working (score: {score:.2f})")
            all_passed = False
        
        return all_passed
        
    except ImportError as e:
        print(f"[FAIL] Cannot import smart context module: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_context_retriever_integration():
    """Test that context_retriever uses smart context."""
    print("\n=== Test 4: Context Retriever Integration ===")
    
    try:
        from backend.modules.context_retriever import expand_code_context
        from backend.modules.smart_context import SMART_CONTEXT_AVAILABLE
        
        if SMART_CONTEXT_AVAILABLE:
            print("[PASS] Smart context is available in context_retriever!")
        else:
            print("[WARN] Smart context not available (may be using fallback)")
        
        # Test that expand_code_context accepts new parameters
        test_evidences = [{
            "file": "test.py",
            "start": 1,
            "end": 10,
            "snippet": "def test(): pass"
        }]
        
        # This should work with new parameters
        try:
            result = expand_code_context(
                test_evidences,
                repo_dir=TEST_REPO,
                context_lines=10,
                use_smart_context=True,
                query="test function",
                max_tokens=1000
            )
            print("[PASS] expand_code_context accepts smart context parameters!")
            return True
        except TypeError as e:
            if "unexpected keyword argument" in str(e):
                print(f"[FAIL] expand_code_context doesn't accept new parameters: {e}")
                return False
            else:
                raise
        
    except Exception as e:
        print(f"[FAIL] Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Smart Context Management Test Suite")
    print("=" * 60)
    
    # Test server health first
    if not test_server_health():
        print("\n[FAIL] Server is not running. Please start it first.")
        sys.exit(1)
    
    # Run tests
    results = []
    
    # Test 1: Chat with smart context
    results.append(test_chat_with_smart_context())
    
    # Test 2: Refactor with file priority
    results.append(test_refactor_with_file_priority())
    
    # Test 3: Smart context module
    results.append(test_smart_context_module())
    
    # Test 4: Context retriever integration
    results.append(test_context_retriever_integration())
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if all(results):
        print("\n[SUCCESS] All tests passed!")
        print("\n✅ Smart Context Management is working correctly!")
        sys.exit(0)
    else:
        print("\n[FAIL] Some tests failed!")
        print("\n⚠️  Please check the errors above and fix any issues.")
        sys.exit(1)
