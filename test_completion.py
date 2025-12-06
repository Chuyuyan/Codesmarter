"""
Test script for the inline code completion endpoint.
"""
import requests
import json
from pathlib import Path

SERVER_URL = "http://127.0.0.1:5050"

def test_completion():
    """Test the /completion endpoint."""
    
    # Example Python file content
    file_content = """def calculate_total(items):
    total = 0
    for item in items:
        total += item['price']
    
    return total

def process_order(order):
    # TODO: implement order processing
    """
    
    file_path = "test_example.py"
    cursor_line = 10  # Position at the end of the TODO comment
    cursor_column = 35  # After "# TODO: implement order processing"
    
    # Test completion endpoint
    print(f"Testing /completion endpoint...")
    print(f"File: {file_path}")
    print(f"Cursor: Line {cursor_line}, Column {cursor_column}")
    print(f"Context: {file_content[:100]}...")
    print()
    
    response = requests.post(
        f"{SERVER_URL}/completion",
        json={
            "file_path": file_path,
            "file_content": file_content,
            "cursor_line": cursor_line,
            "cursor_column": cursor_column,
            "repo_dir": None,  # Optional
            "num_completions": 1,
            "max_tokens": 200
        },
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get("ok"):
            completion = data.get("primary_completion", "")
            print(f"✅ Completion generated ({len(completion)} chars):")
            print("=" * 60)
            print(completion)
            print("=" * 60)
        else:
            print(f"❌ Error: {data.get('error')}")
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    try:
        test_completion()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

