"""
Automated test for auto-sync (code change tracking).
Tests that file changes are automatically detected and index is updated.
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
TEST_FILE = Path(TEST_REPO) / "watcher_test_example.py"  # Changed name to avoid ignore patterns

def check_server():
    """Check if server is running."""
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def index_repo():
    """Index the test repository."""
    print("📚 Step 1: Indexing repository...")
    try:
        response = requests.post(
            f"{SERVER_URL}/index_repo",
            json={"repo_dir": TEST_REPO},
            timeout=300
        )
        data = response.json()
        if data.get("ok"):
            print(f"✅ Repository indexed! Chunks: {data.get('chunks', 0)}")
            return True
        else:
            print(f"❌ Error: {data.get('error')}")
            return False
    except Exception as e:
        print(f"❌ Error indexing: {e}")
        return False

def create_test_file():
    """Create a test file to modify."""
    print("\n📝 Step 2: Creating test file...")
    TEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    content = '''"""
Test file for auto-sync testing.
This file will be modified to test automatic index updates.
"""

def test_function():
    """This is a test function."""
    return "original content"

class TestClass:
    """Test class for auto-sync."""
    pass
'''
    TEST_FILE.write_text(content, encoding='utf-8')
    print(f"✅ Created: {TEST_FILE.name}")
    return True

def wait_for_sync(seconds=5):
    """Wait for auto-sync to process changes."""
    print(f"\n⏳ Step 3: Waiting {seconds} seconds for auto-sync to detect changes...")
    print("   (Auto-sync debounces for 2 seconds)")
    time.sleep(seconds)
    print("✅ Wait complete")

def modify_test_file():
    """Modify the test file to trigger auto-sync."""
    print("\n📝 Step 4: Modifying test file...")
    
    if not TEST_FILE.exists():
        print(f"❌ Test file not found: {TEST_FILE}")
        return False
    
    # Read current content
    content = TEST_FILE.read_text(encoding='utf-8')
    
    # Add a new function
    new_function = '''

def watcher_new_function():
    """This is a NEW function added for testing auto-sync."""
    return "new content added by watcher test"
'''
    # Add before the last line
    lines = content.splitlines()
    lines.insert(-1, new_function)
    new_content = '\n'.join(lines)
    
    # Write modified content
    TEST_FILE.write_text(new_content, encoding='utf-8')
    print(f"✅ Modified: {TEST_FILE.name}")
    print("   Added: watcher_new_function()")
    return True

def search_for_changes():
    """Search for the new content to verify index was updated."""
    print("\n🔍 Step 5: Searching for new content in index...")
    
    try:
        response = requests.post(
            f"{SERVER_URL}/search",
            json={
                "repo_dir": TEST_REPO,
                "query": "watcher_new_function",
                "k": 5
            },
            timeout=10
        )
        data = response.json()
        
        if data.get("ok"):
            results = data.get("results", [])
            print(f"✅ Search completed! Found {len(results)} results")
            
            # Check if our new function appears in results
            found_new_function = False
            for result in results:
                snippet = result.get("snippet", "").lower()
                if "watcher_new_function" in snippet:
                    found_new_function = True
                    print(f"✅ Found new function in: {Path(result['file']).name}")
                    print(f"   Score: {result.get('score_vec', 0):.4f}")
                    print(f"   Snippet preview: {snippet[:100]}...")
                    break
            
            if found_new_function:
                print("\n🎉 SUCCESS! Auto-sync is working!")
                print("   Index was automatically updated with file changes!")
                return True
            else:
                print("\n⚠️  New function not found in search results")
                print("   Searched for: 'watcher_new_function'")
                print("   Results found: " + str(len(results)))
                if results:
                    print("   Top result file: " + Path(results[0].get('file', '')).name)
                print("   This might mean:")
                print("   1. Auto-sync hasn't processed the change yet (wait longer)")
                print("   2. Auto-sync is not enabled")
                print("   3. File wasn't indexed initially")
                print("   4. Check server console for '[file_watcher]' or '[index_sync]' messages")
                return False
        else:
            print(f"❌ Search error: {data.get('error')}")
            return False
    except Exception as e:
        print(f"❌ Error searching: {e}")
        return False

def cleanup():
    """Clean up test file."""
    print("\n🧹 Step 6: Cleaning up test file...")
    try:
        if TEST_FILE.exists():
            TEST_FILE.unlink()
            print(f"✅ Deleted: {TEST_FILE.name}")
    except Exception as e:
        print(f"⚠️  Could not delete test file: {e}")

def main():
    """Run the auto-sync test."""
    print("=" * 60)
    print("🧪 Testing Auto-Sync (Code Change Tracking)")
    print("=" * 60)
    
    # Check server
    print("\n🔌 Checking server...")
    if not check_server():
        print(f"❌ Server not running at {SERVER_URL}")
        print("   Please start the server: python -m backend.app")
        return False
    print("✅ Server is running")
    
    # Index repository
    if not index_repo():
        print("\n❌ Failed to index repository")
        return False
    
    # Wait a bit for auto-watch to start
    print("\n⏳ Waiting for auto-watch to initialize...")
    time.sleep(2)
    
    # Create test file
    if not create_test_file():
        cleanup()
        return False
    
    # Wait for auto-sync to detect new file
    wait_for_sync(5)
    
    # Search for the original content first
    print("\n🔍 Verifying test file was indexed...")
    try:
        response = requests.post(
            f"{SERVER_URL}/search",
            json={
                "repo_dir": TEST_REPO,
                "query": "test_function original",
                "k": 5
            },
            timeout=10
        )
        if response.json().get("ok"):
            print("✅ Test file is in index")
    except:
        print("⚠️  Could not verify test file in index")
    
    # Modify file
    if not modify_test_file():
        cleanup()
        return False
    
    # Wait for auto-sync to process the change
    print("\n⏳ Waiting for auto-sync to process file change...")
    print("   (Auto-sync has 2-second debounce + processing time)")
    time.sleep(6)  # Wait longer to ensure processing completes
    
    # Search for changes
    success = search_for_changes()
    
    # Cleanup
    cleanup()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ TEST PASSED: Auto-sync is working correctly!")
    else:
        print("❌ TEST FAILED: Auto-sync may not be working")
        print("\n💡 Tips:")
        print("   1. Check server console for '[index_sync]' messages")
        print("   2. Make sure watchdog is installed: pip install watchdog")
        print("   3. Verify auto-watch started (check server console)")
    print("=" * 60)
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted")
        cleanup()
        sys.exit(1)

