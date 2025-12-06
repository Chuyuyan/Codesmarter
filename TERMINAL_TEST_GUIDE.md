# Terminal Testing Guide for Completion Feature

## Two Types of Consoles

### 1. Terminal Console (PowerShell/Command Prompt)
**Where:** The terminal where you run Python commands  
**Used for:** Testing backend endpoints, running scripts, starting server

### 2. Developer Console (VS Code)
**Where:** VS Code Developer Tools (`Ctrl+Shift+P` → `Developer: Toggle Developer Tools` → Console tab)  
**Used for:** Debugging VS Code extension, seeing extension logs

---

## Why Ghost Text Might Not Appear

### Common Issues:

1. **Extension Not Loaded**
   - Solution: Reload VS Code window (`Ctrl+R` or `Ctrl+Shift+P` → `Developer: Reload Window`)

2. **Backend Server Not Running**
   - Solution: Start server: `python -m backend.app`

3. **Extension Not Calling Backend**
   - Check Developer Console for errors
   - Check if extension is compiled: `cd vscode-extension && npm run compile`

4. **Need to Actually Type (Not Just Position Cursor)**
   - Inline completions trigger when you TYPE
   - Just positioning cursor won't trigger
   - Type a space or press Enter after positioning cursor

5. **Trigger Conditions Not Met**
   - Completions might not appear if cursor is in middle of a word
   - Try at end of line or after whitespace

---

## Terminal Test Script

### Quick Test from Terminal

**Run this in PowerShell/Terminal:**

```powershell
python test_completion_terminal.py
```

This tests:
- ✅ Backend endpoint is accessible
- ✅ Completion generation works
- ✅ Shows the actual completion that would be sent to VS Code

**If this works:** Backend is fine, issue is with VS Code extension  
**If this fails:** Backend issue, fix that first

---

## Manual Terminal Test

### Test 1: Check Server is Running

```powershell
curl http://127.0.0.1:5050/health
```

**Should return:** `{"ok": true, "port": 5050}`

**Or in PowerShell:**
```powershell
Invoke-WebRequest -Uri http://127.0.0.1:5050/health -UseBasicParsing
```

---

### Test 2: Test Completion Endpoint Directly

**Create a test file** or use PowerShell:

```powershell
$body = @{
    file_path = "test.tsx"
    file_content = "export default function Test() {`n  // TODO: add code`n  if"
    cursor_line = 3
    cursor_column = 3
    num_completions = 1
    max_tokens = 200
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5050/completion -Body $body -ContentType "application/json"
```

**This will show:**
- If backend is working
- What completion would be generated
- Any errors from backend

---

### Test 3: Use Python Script

**Run the test script:**

```powershell
python test_completion_terminal.py
```

**Or:**

```powershell
python test_completion_automated.py
```

**These test:**
- Backend endpoint
- Completion generation
- Error handling
- Performance

---

## Step-by-Step Debugging

### Step 1: Test Backend in Terminal

```powershell
# Terminal 1: Start server
python -m backend.app

# Terminal 2: Run test
python test_completion_terminal.py
```

**If test passes:** Backend is working ✅  
**If test fails:** Fix backend first ❌

---

### Step 2: Check Extension in VS Code

1. **Compile extension:**
   ```powershell
   cd vscode-extension
   npm run compile
   ```

2. **Reload VS Code:**
   - `Ctrl+Shift+P` → `Developer: Reload Window`

3. **Open Developer Console:**
   - `Ctrl+Shift+P` → `Developer: Toggle Developer Tools`
   - Click "Console" tab

4. **Test in VS Code:**
   - Open `page.tsx`
   - Type code after TODO
   - Watch Console tab for `[completion]` messages

5. **If you see `[completion] Requesting...` messages:**
   - Extension is calling backend ✅
   - If ghost text doesn't appear, might be VS Code rendering issue

6. **If you DON'T see messages:**
   - Extension not triggering ❌
   - Check for errors in Console tab
   - Check if extension is loaded

---

## Quick Commands

### Check Server:
```powershell
Invoke-WebRequest -Uri http://127.0.0.1:5050/health -UseBasicParsing
```

### Test Completion:
```powershell
python test_completion_terminal.py
```

### Start Server:
```powershell
python -m backend.app
```

### Compile Extension:
```powershell
cd vscode-extension
npm run compile
```

---

## Expected Behavior

### Terminal Test (Backend):
```
COMPLETION GENERATED:
<code completion here>
Length: 200 characters
SUCCESS: Backend is generating completions!
```

### VS Code Extension:
1. Type code after TODO
2. Wait 1-2 seconds
3. Grayed-out ghost text appears
4. Press Tab to accept

---

## Troubleshooting

### Issue: Terminal test works, but no ghost text in VS Code

**Possible causes:**
1. Extension not loaded → Reload VS Code
2. Extension not compiled → Run `npm run compile`
3. Extension has errors → Check Developer Console
4. Trigger conditions not met → Try typing at different positions

### Issue: Terminal test fails

**Possible causes:**
1. Server not running → Start with `python -m backend.app`
2. Wrong port → Check server is on port 5050
3. Connection error → Check firewall/network

---

## Summary

**Terminal Testing:**
- ✅ Tests backend endpoint directly
- ✅ Shows what completion would be generated
- ✅ Proves backend is working

**VS Code Extension Testing:**
- ⚠️ Requires VS Code UI
- ⚠️ Needs manual interaction
- ⚠️ Check Developer Console for logs

**Best Practice:**
1. First: Test in terminal (verify backend)
2. Then: Test in VS Code (verify extension)

---

**Created:** `test_completion_terminal.py` - Run this to test backend from terminal!

