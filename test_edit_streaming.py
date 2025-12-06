"""
Test script for the direct code editing endpoint with streaming support.
"""
import requests
import json
import sys

SERVER_URL = "http://127.0.0.1:5050"

def test_streaming_edit():
    """Test streaming code editing."""
    print("\n=== Test 1: Streaming Code Editing ===")
    
    selected_code = """def calculate_total(items):
    total = 0
    for item in items:
        if 'price' not in item:
            raise ValueError(f"Item missing 'price' key: {item}")
        total += item['price']
    return total"""
    
    instruction = "Add type hints and improve error handling"
    
    try:
        response = requests.post(
            f"{SERVER_URL}/edit",
            json={
                "selected_code": selected_code,
                "instruction": instruction,
                "file_path": "example.py",
                "repo_dir": "C:\\Users\\57811\\my-portfolio",
                "stream": True
            },
            stream=True,
            timeout=180
        )
        
        if response.status_code == 200:
            print("[PASS] Streaming connection established!")
            print("\nReceiving chunks...")
            
            chunks = []
            metadata = None
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # Remove 'data: ' prefix
                        try:
                            data = json.loads(data_str)
                            
                            if data.get("type") == "start":
                                print("  [START] Stream started")
                            elif data.get("type") == "chunk":
                                chunk = data.get("content", "")
                                chunks.append(chunk)
                                print(f"  [CHUNK] Received {len(chunk)} chars (total: {sum(len(c) for c in chunks)} chars)")
                            elif data.get("type") == "done":
                                metadata = data
                                print(f"  [DONE] Stream completed")
                                print(f"    File Path: {metadata.get('file_path')}")
                                print(f"    Language: {metadata.get('language')}")
                                print(f"    Lines Added: {metadata.get('lines_added')}")
                                print(f"    Lines Removed: {metadata.get('lines_removed')}")
                                print(f"    Instruction: {metadata.get('instruction')}")
                            elif data.get("type") == "error":
                                print(f"  [ERROR] {data.get('error')}")
                                return False
                        except json.JSONDecodeError as e:
                            print(f"  [WARN] Failed to parse JSON: {e}")
                            print(f"  Raw data: {data_str[:100]}")
            
            edited_code = "".join(chunks)
            
            if edited_code and metadata:
                print("\n" + "=" * 60)
                print("Original Code:")
                print("=" * 60)
                print(selected_code)
                print("\n" + "=" * 60)
                print("Edited Code:")
                print("=" * 60)
                print(edited_code[:1000])
                if len(edited_code) > 1000:
                    print(f"\n... (truncated, total {len(edited_code)} chars)")
                print("=" * 60)
                print(f"\n[PASS] Streaming test completed successfully!")
                print(f"Total chunks: {len(chunks)}")
                print(f"Total length: {len(edited_code)} chars")
                return True
            else:
                print("[FAIL] No edited code or metadata received")
                return False
        else:
            print(f"[FAIL] HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("[FAIL] Request timed out after 180 seconds")
        return False
    except Exception as e:
        print(f"[FAIL] Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_non_streaming_edit():
    """Test non-streaming code editing (backward compatibility)."""
    print("\n=== Test 2: Non-Streaming Code Editing (Backward Compatibility) ===")
    
    selected_code = """def calculate_total(items):
    total = 0
    for item in items:
        if 'price' not in item:
            raise ValueError(f"Item missing 'price' key: {item}")
        total += item['price']
    return total"""
    
    instruction = "Add type hints to parameters and return value"
    
    try:
        response = requests.post(
            f"{SERVER_URL}/edit",
            json={
                "selected_code": selected_code,
                "instruction": instruction,
                "file_path": "example.py",
                "repo_dir": "C:\\Users\\57811\\my-portfolio",
                "stream": False  # Explicitly non-streaming
            },
            timeout=180
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                print("[PASS] Non-streaming mode works!")
                print(f"File Path: {data.get('file_path')}")
                print(f"Language: {data.get('language')}")
                print(f"Lines Added: {data.get('lines_added')}")
                print(f"Lines Removed: {data.get('lines_removed')}")
                print(f"\nOriginal Code:")
                print("=" * 60)
                print(data.get('original_code', '')[:500])
                print("=" * 60)
                print(f"\nEdited Code (first 500 chars):")
                print("=" * 60)
                edited = data.get('edited_code', '')
                print(edited[:500])
                if len(edited) > 500:
                    print(f"\n... (truncated, total {len(edited)} chars)")
                print("=" * 60)
                
                # Show diff preview
                diff = data.get('diff', '')
                if diff:
                    print(f"\nDiff Preview (first 300 chars):")
                    print("=" * 60)
                    print(diff[:300])
                    if len(diff) > 300:
                        print(f"\n... (truncated, total {len(diff)} chars)")
                    print("=" * 60)
                
                return True
            else:
                print(f"[FAIL] Error: {data.get('error')}")
                return False
        else:
            print(f"[FAIL] HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("[FAIL] Request timed out after 180 seconds")
        return False
    except Exception as e:
        print(f"[FAIL] Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


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


if __name__ == "__main__":
    print("=" * 60)
    print("Direct Code Editing Streaming Test")
    print("=" * 60)
    
    # Test server health first
    if not test_server_health():
        print("\n[FAIL] Server is not running. Please start it first.")
        sys.exit(1)
    
    # Run tests
    results = []
    
    # Test 1: Streaming mode
    results.append(test_streaming_edit())
    
    # Test 2: Non-streaming mode (backward compatibility)
    results.append(test_non_streaming_edit())
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if all(results):
        print("\n[SUCCESS] All tests passed!")
        sys.exit(0)
    else:
        print("\n[FAIL] Some tests failed!")
        sys.exit(1)

