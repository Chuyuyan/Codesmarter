# Testing Inline Code Completion (Tab Feature)

## Quick Test Steps

### ✅ Option 1: Test in TypeScript File (EASIEST)
1. **Open `page.tsx`** (already TypeScript - shown in your screenshot)
2. **Go to the end of a function** (e.g., after line 29 in the Card function)
3. **Type something like:**
   ```typescript
   // TODO: add error handling
   ```
4. **Wait 1-2 seconds** (API call to backend)
5. **Look for grayed-out ghost text** appearing after your cursor
6. **Press Tab** to accept the suggestion

### ✅ Option 2: Test in Python File
1. **Create a new file: `test.py`**
2. **Type this code:**
   ```python
   def calculate_total(items):
       total = 0
       for item in items:
           total += item['price']
       return total

   def process_order(order):
       # TODO: implement order processing
       ```
3. **Position cursor at the end of the TODO comment**
4. **Wait for ghost text** to appear
5. **Press Tab** to accept

### ✅ Option 3: Set Language Mode for 'test' File
1. **Click on `test` tab**
2. **Press: `Ctrl+K M`** (or Cmd+K M on Mac)
3. **Type: `Python`** and press Enter
4. **Status bar should now show "Python"** instead of "Plain Text"
5. **Start typing code** - completions should appear

## What to Look For

### ✅ Working Correctly:
- **Grayed-out ghost text** appears inline (like Cursor)
- **Slight delay** after typing (1-2 seconds for API call)
- **Ghost text** is after your cursor position
- **Press Tab** to accept the suggestion
- **Ghost text disappears** if you continue typing

### ❌ Not Working:
- No ghost text appears
- Completions appear in dropdown (wrong - should be inline)
- Error messages in console

## Debugging Steps

### 1. Check Extension is Loaded
- Open **Output panel** (`Ctrl+Shift+U`)
- Select **"Log (Extension Host)"**
- Should see: `Code Assistant extension is now active!`
- Should see: `Inline Completion Provider (Tab feature - like Cursor)`

### 2. Check Backend Server
- Make sure server is running: `python -m backend.app`
- Test: `http://127.0.0.1:5050/health`
- Should return: `{"status": "ok"}`

### 3. Check Console Logs
In **Output panel** → **"Log (Extension Host)"**, look for:
```
[completion] Requesting inline completion for page.tsx:10:35
[completion] Generated inline completion (246 chars): ...
```

If you see these messages, the extension is calling the backend!

### 4. Check Repository Index
- Make sure repository is indexed
- Run command: **"Code Assistant: Index Repository"**
- Should see success message

### 5. Check Configuration
- Settings (`Ctrl+,`)
- Search: `codeAssistant.enableInlineCompletion`
- Should be **enabled (true)**

## Common Issues

### Issue: File is in "Plain Text" mode
**Solution:** Set language mode (`Ctrl+K M`) → Select Python/TypeScript

### Issue: No completions appear
**Check:**
- Backend server running?
- Repository indexed?
- Extension loaded? (check logs)
- Configuration enabled?

### Issue: Completions appear in dropdown instead of inline
**Solution:** This is wrong - should use `InlineCompletionItemProvider`. Check extension code.

### Issue: "Extension not found" error
**Solution:** 
- Compile extension: `cd vscode-extension && npm run compile`
- Reload VS Code window

## Expected Behavior (Like Cursor)

1. **You type code** → e.g., `def calculate_total(items):`
2. **You add a TODO** → e.g., `# TODO: implement logic`
3. **Ghost text appears** → Grayed-out completion text
4. **Press Tab** → Completion is inserted
5. **Continue coding** → Cycle repeats

## Test Example

Try this in `page.tsx`:

```typescript
function testFunction() {
    // TODO: add validation
    // <-- Cursor here, ghost text should appear suggesting code
}
```

Or in a Python file:

```python
def process_data(data):
    # TODO: validate input
    # <-- Cursor here, should see completion suggestion
```

---

**Note:** The backend endpoint is confirmed working (test_completion.py passed). Now test the VS Code integration!

