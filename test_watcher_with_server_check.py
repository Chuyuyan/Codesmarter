"""
Test that also checks server console logs via API.
This way we can see if the server is detecting changes even if we can't see console directly.
"""
import sys
import time
import requests
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

SERVER_URL = "http://127.0.0.1:5050"
TEST_REPO = Path(r"C:\Users\57811\my-portfolio")
TEST_FILE = TEST_REPO / "simple_watcher_test.py"

def check_server_health():
    """Check if server is responding."""
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

print("="*60)
print("🔍 WATCHER TEST WITH SERVER CHECK")
print("="*60)

# Check server
print("\n🔌 Checking server...")
if not check_server_health():
    print("❌ Server not running!")
    print("   Start it in another terminal: python -m backend.app")
    sys.exit(1)
print("✅ Server is running")

print("\n" + "="*60)
print("📋 IMPORTANT: Where is the Server Console?")
print("="*60)
print("\nThe server console is the TERMINAL/POWERSHELL window where you ran:")
print("   python -m backend.app")
print("\nYou should see output like:")
print("   * Running on http://127.0.0.1:5050")
print("   [index_repo] Starting indexing...")
print("\n💡 Keep that terminal window visible!")
print("   That's where file watcher messages will appear.")
print("\n" + "="*60)

input("\n⏸️  Press Enter when you have the server console visible...")

# Clean up old file
if TEST_FILE.exists():
    TEST_FILE.unlink()

print(f"\n📝 Creating test file: {TEST_FILE.name}")
print("   File path: " + str(TEST_FILE))
TEST_FILE.write_text('def test_function(): return "test"', encoding='utf-8')
print("✅ File created!")

print("\n" + "="*60)
print("👀 WATCH YOUR SERVER CONSOLE NOW!")
print("="*60)
print("\nIn the terminal where you ran 'python -m backend.app',")
print("you should see messages like:")
print("\n   [file_watcher] Event detected: created - simple_watcher_test.py")
print("   [file_watcher] Queuing event: created - ...")
print("   [file_watcher] Processing event: created - ...")
print("   [index_sync] File created: simple_watcher_test.py")
print("   [index_sync] Updated index for simple_watcher_test.py (X chunks)")
print("\n⏳ Waiting 10 seconds...")

for i in range(10, 0, -1):
    print(f"   {i}...", end=' ')
    time.sleep(1)
    if i % 2 == 0:
        print()

print("\n" + "="*60)
print("❓ WHAT DID YOU SEE IN SERVER CONSOLE?")
print("="*60)
print("\nChoose:")
print("   1. I saw [file_watcher] messages")
print("   2. I saw [index_sync] messages")
print("   3. I saw BOTH [file_watcher] AND [index_sync] messages")
print("   4. I saw NOTHING - no messages at all")
print("   5. I saw ERROR messages")
print("\n💡 Tell me which number you saw!")

# Also check if file was indexed by searching
print("\n🔍 Checking if file was indexed...")
time.sleep(2)  # Wait a bit more for processing
try:
    response = requests.post(
        f"{SERVER_URL}/search",
        json={
            "repo_dir": str(TEST_REPO),
            "query": "test_function",
            "k": 5
        },
        timeout=10
    )
    data = response.json()
    if data.get("ok"):
        results = data.get("results", [])
        found = any("simple_watcher_test" in r.get("file", "") or "test_function" in r.get("snippet", "") for r in results)
        if found:
            print("✅ File found in search results!")
            print("   This means it was indexed (auto-sync might be working)")
        else:
            print("⚠️  File NOT in search results yet")
            print("   This might mean auto-sync hasn't processed it")
    else:
        print(f"⚠️  Search error: {data.get('error')}")
except Exception as e:
    print(f"⚠️  Error checking search: {e}")

# Cleanup
print("\n🧹 Cleaning up...")
if TEST_FILE.exists():
    TEST_FILE.unlink()
    print(f"✅ Deleted: {TEST_FILE.name}")

print("\n" + "="*60)
print("✅ Test complete!")
print("="*60)
print("\n💡 Next steps:")
print("   - If you saw [file_watcher] messages: Watcher is detecting files!")
print("   - If you saw [index_sync] messages: Index is being updated!")
print("   - If you saw nothing: Watcher might not be running or detecting files")
print("   - Share what you saw and we'll debug from there!")

