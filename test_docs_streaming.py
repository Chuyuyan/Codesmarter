"""
Test script for the documentation generation endpoint with streaming support.
"""
import requests
import json
import sys

SERVER_URL = "http://127.0.0.1:5050"

def test_streaming_docstring():
    """Test streaming docstring generation."""
    print("\n=== Test 1: Streaming Docstring Generation ===")
    
    code_snippet = """def calculate_total(items):
    total = 0
    for item in items:
        if 'price' not in item:
            raise ValueError(f"Item missing 'price' key: {item}")
        total += item['price']
    return total"""
    
    try:
        response = requests.post(
            f"{SERVER_URL}/generate_docs",
            json={
                "doc_type": "docstring",
                "code_snippet": code_snippet,
                "doc_format": "google",
                "target_name": "calculate_total",
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
                                print(f"    Doc Type: {metadata.get('doc_type')}")
                                print(f"    Format: {metadata.get('doc_format')}")
                                print(f"    Language: {metadata.get('language')}")
                                print(f"    Target: {metadata.get('target_name')}")
                                print(f"    Lines: {metadata.get('lines')}")
                            elif data.get("type") == "error":
                                print(f"  [ERROR] {data.get('error')}")
                                return False
                        except json.JSONDecodeError as e:
                            print(f"  [WARN] Failed to parse JSON: {e}")
                            print(f"  Raw data: {data_str[:100]}")
            
            documentation = "".join(chunks)
            
            if documentation and metadata:
                print("\n" + "=" * 60)
                print("Generated Documentation:")
                print("=" * 60)
                print(documentation[:800])
                if len(documentation) > 800:
                    print(f"\n... (truncated, total {len(documentation)} chars)")
                print("=" * 60)
                print(f"\n[PASS] Streaming test completed successfully!")
                print(f"Total chunks: {len(chunks)}")
                print(f"Total length: {len(documentation)} chars")
                return True
            else:
                print("[FAIL] No documentation or metadata received")
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


def test_non_streaming_docstring():
    """Test non-streaming docstring generation (backward compatibility)."""
    print("\n=== Test 2: Non-Streaming Docstring Generation (Backward Compatibility) ===")
    
    code_snippet = """def calculate_total(items):
    total = 0
    for item in items:
        if 'price' not in item:
            raise ValueError(f"Item missing 'price' key: {item}")
        total += item['price']
    return total"""
    
    try:
        response = requests.post(
            f"{SERVER_URL}/generate_docs",
            json={
                "doc_type": "docstring",
                "code_snippet": code_snippet,
                "doc_format": "google",
                "target_name": "calculate_total",
                "repo_dir": "C:\\Users\\57811\\my-portfolio",
                "stream": False  # Explicitly non-streaming
            },
            timeout=180
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                print("[PASS] Non-streaming mode works!")
                print(f"Format: {data.get('doc_format')}")
                print(f"Language: {data.get('language')}")
                print(f"Target: {data.get('target_name')}")
                print(f"Lines: {data.get('lines')}")
                print(f"\nGenerated Documentation (first 800 chars):")
                print("=" * 60)
                doc = data.get('documentation', '')
                print(doc[:800])
                if len(doc) > 800:
                    print(f"\n... (truncated, total {len(doc)} chars)")
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
    print("Documentation Generation Streaming Test")
    print("=" * 60)
    
    # Test server health first
    if not test_server_health():
        print("\n❌ Server is not running. Please start it first.")
        sys.exit(1)
    
    # Run tests
    results = []
    
    # Test 1: Streaming mode
    results.append(test_streaming_docstring())
    
    # Test 2: Non-streaming mode (backward compatibility)
    results.append(test_non_streaming_docstring())
    
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

