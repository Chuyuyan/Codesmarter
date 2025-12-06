"""
Test script for full-stack project generation.
Tests the /generate_project endpoint.
"""
import requests
import json
import sys
from pathlib import Path

BASE_URL = "http://127.0.0.1:5050"


def test_server_health():
    """Test if server is running."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=15)
        if response.status_code == 200:
            print("[PASS] Server is running")
            return True
        else:
            print(f"[FAIL] Server returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[FAIL] Server is not running: {e}")
        print("Please start the server: python -m backend.app")
        return False


def test_generate_project_preview():
    """Test full-stack project generation in preview mode."""
    print("\n" + "="*60)
    print("Test: Full-Stack Project Generation (Preview)")
    print("="*60)
    
    description = "Build me a todo app with React frontend, Flask backend, and SQLite database"
    repo_path = str(Path.home() / "test-todo-app")
    
    # Test with streaming enabled (prevents timeouts)
    payload = {
        "description": description,
        "repo_path": repo_path,
        "dry_run": True,
        "apply": False,
        "stream": True  # Enable streaming to avoid timeouts
    }
    
    try:
        print(f"\nRequest: {description}")
        print(f"Target: {repo_path}")
        print(f"Streaming: Enabled (to avoid timeouts)")
        
        # Use streaming endpoint
        response = requests.post(
            f"{BASE_URL}/generate_project",
            json=payload,
            timeout=600,  # 10 minutes for generation
            stream=True  # Enable streaming response
        )
        
        if response.status_code == 200:
            # Handle streaming response (SSE)
            print("\n[INFO] Receiving streaming response...")
            print("-" * 60)
            
            progress_messages = []
            chunks = []
            final_result = None
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])  # Remove 'data: ' prefix
                            event_type = data.get('type')
                            
                            if event_type == 'start':
                                print("[START] Generation started")
                            elif event_type == 'progress':
                                msg = data.get('message', '').strip()
                                if msg:
                                    progress_messages.append(msg)
                                    # Print progress (but limit output)
                                    if len(progress_messages) <= 10 or 'complete' in msg.lower() or 'error' in msg.lower():
                                        print(f"[PROGRESS] {msg}")
                            elif event_type == 'chunk':
                                chunks.append(data.get('content', ''))
                            elif event_type == 'done':
                                final_result = data
                                print("[DONE] Generation completed!")
                            elif event_type == 'error':
                                print(f"\n[ERROR] {data.get('error', 'Unknown error')}")
                                return False
                        except json.JSONDecodeError:
                            pass
            
            if final_result and final_result.get('ok'):
                print("\n[PASS] Project generation successful!")
                print(f"\nStack Detected:")
                stack = final_result.get("stack", {})
                print(f"  Frontend: {stack.get('frontend', 'N/A')}")
                print(f"  Backend: {stack.get('backend', 'N/A')}")
                print(f"  Database: {stack.get('database', 'N/A')}")
                
                print(f"\nFeatures: {final_result.get('features', [])}")
                print(f"Total Files: {final_result.get('total_files', 0)}")
                print(f"\nProgress Messages: {len(progress_messages)}")
                print(f"Content Chunks: {len(chunks)}")
                
                return True
            else:
                error_msg = final_result.get('error', 'Unknown error') if final_result else 'No result received'
                print(f"\n[FAIL] Generation failed: {error_msg}")
                return False
        else:
            print(f"\n[FAIL] HTTP {response.status_code}: {response.text[:500]}")
            return False
    
    except requests.exceptions.Timeout:
        print("\n[FAIL] Request timed out (generation took too long)")
        return False
    except Exception as e:
        print(f"\n[FAIL] Exception: {e}")
        return False


def test_analysis_type_detection():
    """Test that 'generate' is auto-detected from questions."""
    print("\n" + "="*60)
    print("Test: Analysis Type Auto-Detection (Generate)")
    print("="*60)
    
    test_questions = [
        "Build me a todo app with React and Flask",
        "Create a blog with authentication",
        "I want to build a full-stack e-commerce site",
        "Generate a project with frontend and backend"
    ]
    
    from backend.modules.analysis_detector import detect_analysis_type
    
    passed = 0
    for question in test_questions:
        detected = detect_analysis_type(question, use_llm=False)
        status = "[PASS]" if detected == "generate" else "[FAIL]"
        print(f"{status} '{question[:50]}...' → {detected}")
        if detected == "generate":
            passed += 1
    
    print(f"\nResults: {passed}/{len(test_questions)} passed")
    return passed == len(test_questions)


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Full-Stack Project Generation Test Suite")
    print("="*60)
    
    # Test 1: Server health
    if not test_server_health():
        print("\n[SKIP] Skipping other tests - server not running")
        return
    
    # Test 2: Analysis type detection
    test_analysis_type_detection()
    
    # Test 3: Project generation (preview)
    print("\n" + "="*60)
    print("Note: Full project generation test may take 2-5 minutes")
    print("This is a preview test - no files will be created")
    print("="*60)
    
    # Auto-run the test (no user input required)
    print("\n[INFO] Running full-stack generation test automatically...")
    test_generate_project_preview()
    
    print("\n" + "="*60)
    print("Test Suite Complete")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

