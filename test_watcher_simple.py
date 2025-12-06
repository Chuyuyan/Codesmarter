"""
Simple test - just create a file and wait, then check server console.
This helps identify if watcher is even detecting events.
"""
import sys
import time
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

TEST_REPO = Path(r"C:\Users\57811\my-portfolio")
TEST_FILE = TEST_REPO / "simple_watcher_test.py"

print("="*60)
print("🔍 SIMPLE WATCHER TEST")
print("="*60)
print("\nThis will create a file and wait 10 seconds.")
print("Watch your SERVER CONSOLE for messages!")
print("\nYou should see messages like:")
print("  [file_watcher] Event detected: created - simple_watcher_test.py")
print("  [index_sync] File created: simple_watcher_test.py")

# Clean up old file
if TEST_FILE.exists():
    TEST_FILE.unlink()

print(f"\n📝 Creating file: {TEST_FILE.name}")
TEST_FILE.write_text('def test(): pass', encoding='utf-8')
print("✅ File created!")

print("\n⏳ Waiting 10 seconds...")
print("👀 WATCH YOUR SERVER CONSOLE NOW!")
print("   Look for '[file_watcher]' or '[index_sync]' messages")

for i in range(10, 0, -1):
    print(f"   {i}...", end=' ')
    time.sleep(1)
    if i % 2 == 0:
        print()

print("\n\n❓ Did you see any messages in server console?")
print("   - '[file_watcher]' messages?")
print("   - '[index_sync]' messages?")
print("   - Or nothing at all?")

# Cleanup
if TEST_FILE.exists():
    print(f"\n🧹 Cleaning up: deleting {TEST_FILE.name}")
    TEST_FILE.unlink()

print("\n✅ Test complete. Check what you saw in server console!")

