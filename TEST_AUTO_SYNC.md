# Testing Auto-Sync (Code Change Tracking)

## Automated Test

I've created an automated test script that will test the auto-sync feature without requiring manual file editing.

### Test Script: `test_auto_sync.py`

This script automatically:
1. ✅ Checks if server is running
2. ✅ Indexes the repository
3. ✅ Creates a test file programmatically
4. ✅ Waits for auto-sync to detect it
5. ✅ Modifies the test file programmatically
6. ✅ Waits for auto-sync to process the change
7. ✅ Searches the index to verify it was updated
8. ✅ Cleans up the test file

### How to Run the Test

**Prerequisites:**
1. Backend server must be running:
   ```powershell
   python -m backend.app
   ```

2. Install watchdog (if not already installed):
   ```powershell
   pip install watchdog
   ```

3. Install requests (for test script):
   ```powershell
   pip install requests
   ```

**Run the test:**
```powershell
python test_auto_sync.py
```

### What the Test Does

1. **Checks Server** - Verifies backend is running
2. **Indexes Repository** - Indexes `C:\Users\57811\my-portfolio`
3. **Creates Test File** - Creates `test_auto_sync_temp.py` with test code
4. **Waits** - Waits for auto-sync to detect and index the new file
5. **Modifies File** - Adds a new function `new_test_function()` to the file
6. **Waits for Update** - Waits for auto-sync to process the change (6 seconds)
7. **Verifies Update** - Searches for "new_test_function" in the index
8. **Reports Result** - Shows whether auto-sync worked or not
9. **Cleans Up** - Deletes the test file

### Expected Output

**If auto-sync is working:**
```
🧪 Testing Auto-Sync (Code Change Tracking)
============================================================

🔌 Checking server...
✅ Server is running

📚 Step 1: Indexing repository...
✅ Repository indexed! Chunks: 19

⏳ Waiting for auto-watch to initialize...

📝 Step 2: Creating test file...
✅ Created: test_auto_sync_temp.py

⏳ Step 3: Waiting 5 seconds for auto-sync to detect changes...
✅ Wait complete

🔍 Verifying test file was indexed...
✅ Test file is in index

📝 Step 4: Modifying test file...
✅ Modified: test_auto_sync_temp.py
   Added: new_test_function()

⏳ Waiting for auto-sync to process file change...
   (Auto-sync has 2-second debounce + processing time)

🔍 Step 5: Searching for new content in index...
✅ Search completed! Found 1 results
✅ Found new function in: test_auto_sync_temp.py
   Score: 0.8234

🎉 SUCCESS! Auto-sync is working!
   Index was automatically updated with file changes!

🧹 Step 6: Cleaning up test file...
✅ Deleted: test_auto_sync_temp.py

============================================================
✅ TEST PASSED: Auto-sync is working correctly!
```

### Troubleshooting

**If test fails:**

1. **Check server console** - Look for messages like:
   - `[index_sync] Started watching repository: my-portfolio`
   - `[index_sync] File modified: test_auto_sync_temp.py`
   - `[index_sync] Updated index for test_auto_sync_temp.py`

2. **Check watchdog installation:**
   ```powershell
   python -c "import watchdog; print('✅ watchdog installed')"
   ```

3. **Check auto-watch started:**
   - After indexing, check server console for: "Started auto-sync for repository"
   - If not present, auto-watch may not have started

4. **Increase wait time:**
   - If test fails, the auto-sync might need more time
   - Edit `test_auto_sync.py` and increase the sleep times

### Manual Testing (Alternative)

If you prefer to test manually:

1. **Index repository** (if not already indexed)
2. **Check server console** - Should see: "Started auto-sync for repository"
3. **Edit any code file** in your repository
4. **Wait 2-3 seconds**
5. **Check server console** - Should see: "[index_sync] File modified: ..."
6. **Ask a question** about the changed code
7. **Verify answer** reflects your changes

---

**Ready to test?** Run: `python test_auto_sync.py`

