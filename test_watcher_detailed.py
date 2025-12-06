"""
Detailed step-by-step test for auto-sync debugging.
Tests each part individually to find the problem.
"""
import sys
import time
import requests
from pathlib import Path

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

SERVER_URL = "http://127.0.0.1:5050"
TEST_REPO = r"C:\Users\57811\my-portfolio"
TEST_FILE = Path(TEST_REPO) / "watcher_test_file.py"

def step1_check_server():
    """Step 1: Check if server is running."""
    print("\n" + "="*60)
    print("STEP 1: Check Server")
    print("="*60)
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=2)
        if response.status_code == 200:
            print("✅ Server is running")
            return True
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server not reachable: {e}")
        return False

def step2_check_watchdog():
    """Step 2: Check if watchdog is installed."""
    print("\n" + "="*60)
    print("STEP 2: Check Watchdog Installation")
    print("="*60)
    try:
        import watchdog
        print(f"✅ watchdog is installed (version: {watchdog.__version__})")
        return True
    except ImportError:
        print("❌ watchdog is NOT installed")
        print("   Install with: pip install watchdog")
        return False

def step3_index_and_check_watcher():
    """Step 3: Index repository and check if watcher starts."""
    print("\n" + "="*60)
    print("STEP 3: Index Repository and Check Watcher")
    print("="*60)
    print("📚 Indexing repository...")
    try:
        response = requests.post(
            f"{SERVER_URL}/index_repo",
            json={"repo_dir": TEST_REPO},
            timeout=300
        )
        data = response.json()
        if data.get("ok"):
            print(f"✅ Repository indexed! Chunks: {data.get('chunks', 0)}")
            print("\n💡 CHECK SERVER CONSOLE NOW!")
            print("   You should see:")
            print("   - '[file_watcher] Started watching: ...'")
            print("   - '[index_sync] Started watching repository: ...'")
            print("\n   Do you see these messages? (y/n)")
            return True
        else:
            print(f"❌ Error indexing: {data.get('error')}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def step4_create_file_and_watch():
    """Step 4: Create a test file and see if watcher detects it."""
    print("\n" + "="*60)
    print("STEP 4: Create File and Check Detection")
    print("="*60)
    
    # Clean up old test file
    if TEST_FILE.exists():
        TEST_FILE.unlink()
    
    print(f"📝 Creating test file: {TEST_FILE.name}")
    content = '''"""Test file for watcher."""
def test_function():
    return "test"
'''
    TEST_FILE.write_text(content, encoding='utf-8')
    print(f"✅ File created")
    
    print("\n⏳ Waiting 5 seconds...")
    print("💡 WATCH SERVER CONSOLE NOW!")
    print("   You should see:")
    print("   - '[file_watcher] Event detected: created - watcher_test_file.py'")
    print("   - '[file_watcher] Queuing event: created - ...'")
    print("   - '[file_watcher] Processing event: created - ...'")
    print("   - '[index_sync] File created: watcher_test_file.py'")
    print("\n   What messages do you see? (describe or copy here)")
    
    time.sleep(5)
    
    # Check if file was indexed
    print("\n🔍 Checking if file was indexed...")
    try:
        response = requests.post(
            f"{SERVER_URL}/search",
            json={
                "repo_dir": TEST_REPO,
                "query": "test_function",
                "k": 5
            },
            timeout=10
        )
        data = response.json()
        if data.get("ok"):
            results = data.get("results", [])
            found = any("watcher_test_file" in r.get("file", "") for r in results)
            if found:
                print("✅ File found in index!")
            else:
                print("⚠️  File NOT found in index yet")
                print("   This might mean auto-sync hasn't processed it yet")
        else:
            print(f"⚠️  Search error: {data.get('error')}")
    except Exception as e:
        print(f"⚠️  Error searching: {e}")
    
    return True

def step5_modify_file_and_watch():
    """Step 5: Modify file and see if watcher detects change."""
    print("\n" + "="*60)
    print("STEP 5: Modify File and Check Detection")
    print("="*60)
    
    if not TEST_FILE.exists():
        print("❌ Test file doesn't exist, creating it first...")
        step4_create_file_and_watch()
        time.sleep(3)
    
    print(f"📝 Modifying test file: {TEST_FILE.name}")
    content = TEST_FILE.read_text(encoding='utf-8')
    content += '\n\ndef new_function_added_by_test():\n    return "new function"\n'
    TEST_FILE.write_text(content, encoding='utf-8')
    print("✅ File modified (added new_function_added_by_test)")
    
    print("\n⏳ Waiting 8 seconds for auto-sync to process...")
    print("💡 WATCH SERVER CONSOLE NOW!")
    print("   You should see:")
    print("   - '[file_watcher] Event detected: modified - watcher_test_file.py'")
    print("   - '[index_sync] File modified: watcher_test_file.py'")
    print("   - '[index_sync] Updated index for watcher_test_file.py (X chunks)'")
    print("\n   What messages appear? (describe or copy)")
    
    time.sleep(8)
    
    # Check if modification is in index
    print("\n🔍 Checking if modification is in index...")
    try:
        response = requests.post(
            f"{SERVER_URL}/search",
            json={
                "repo_dir": TEST_REPO,
                "query": "new_function_added_by_test",
                "k": 5
            },
            timeout=10
        )
        data = response.json()
        if data.get("ok"):
            results = data.get("results", [])
            found = any("new_function_added_by_test" in r.get("snippet", "").lower() for r in results)
            if found:
                print("✅ Modification found in index! Auto-sync is working!")
                return True
            else:
                print("❌ Modification NOT found in index")
                print("   Auto-sync might not be working")
                return False
        else:
            print(f"❌ Search error: {data.get('error')}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def step6_cleanup():
    """Step 6: Clean up test file."""
    print("\n" + "="*60)
    print("STEP 6: Cleanup")
    print("="*60)
    try:
        if TEST_FILE.exists():
            TEST_FILE.unlink()
            print(f"✅ Deleted test file: {TEST_FILE.name}")
    except Exception as e:
        print(f"⚠️  Could not delete test file: {e}")

def main():
    """Run detailed diagnostic test."""
    print("="*60)
    print("🔍 DETAILED AUTO-SYNC DIAGNOSTIC TEST")
    print("="*60)
    print("\nThis test will check each part step-by-step.")
    print("Pay attention to the SERVER CONSOLE for messages!")
    
    # Step 1: Check server
    if not step1_check_server():
        print("\n❌ Server not running. Start it first!")
        return False
    
    # Step 2: Check watchdog
    if not step2_check_watchdog():
        print("\n❌ Install watchdog first!")
        return False
    
    # Step 3: Index and check watcher
    if not step3_index_and_check_watcher():
        print("\n❌ Failed to index repository")
        return False
    
    input("\n⏸️  Press Enter after checking server console for watcher messages...")
    
    # Step 4: Create file
    step4_create_file_and_watch()
    
    input("\n⏸️  Press Enter after checking server console for file creation messages...")
    
    # Step 5: Modify file
    success = step5_modify_file_and_watch()
    
    # Step 6: Cleanup
    step6_cleanup()
    
    print("\n" + "="*60)
    if success:
        print("✅ DIAGNOSTIC COMPLETE: Auto-sync appears to be working!")
    else:
        print("❌ DIAGNOSTIC COMPLETE: Issues found")
        print("\n💡 Based on what you saw in server console:")
        print("   - If NO file_watcher messages: Watcher not detecting files")
        print("   - If file_watcher but NO index_sync: Update process failing")
        print("   - If index_sync but NOT in search: Index save failing")
    print("="*60)
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted")
        step6_cleanup()
        sys.exit(1)

