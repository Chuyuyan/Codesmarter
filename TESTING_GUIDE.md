# Testing Inline Code Completion

## Automated Testing vs. Manual Testing

### ✅ Automated Testing (What We Can Do)

**Backend Endpoint Testing:**
- ✅ Test completion endpoint directly
- ✅ Test various code scenarios
- ✅ Test error handling
- ✅ Test performance
- ✅ Validate API responses

**Run automated tests:**
```powershell
python test_completion_automated.py
```

This tests:
1. Server health check
2. Basic Python completion
3. TypeScript completion
4. Multiple completions
5. Error handling
6. Performance benchmarks

---

### ⚠️ Manual Testing (Required for VS Code Extension)

**VS Code Extension Integration:**
- ⚠️ Must test manually in VS Code
- ⚠️ Requires VS Code Extension Development Host
- ⚠️ Need to see actual ghost text behavior
- ⚠️ Need to test Tab key acceptance

**Why manual testing is needed:**
- VS Code extension runs in a separate process
- InlineCompletionItemProvider is part of VS Code's UI system
- Ghost text rendering requires VS Code's rendering engine
- User interaction (Tab key) needs actual VS Code interface

---

## Testing Strategy

### Phase 1: Automated Backend Tests ✅

**Run this first:**
```powershell
# Make sure server is running
python -m backend.app

# In another terminal
python test_completion_automated.py
```

**What it tests:**
- ✅ Backend endpoint works
- ✅ Completions are generated
- ✅ Error handling works
- ✅ Performance is acceptable

**If all tests pass:** Backend is working! ✅

---

### Phase 2: Manual VS Code Testing ⚠️

**After backend tests pass, test in VS Code:**

1. **Compile extension:**
   ```powershell
   cd vscode-extension
   npm run compile
   ```

2. **Open Extension Development Host:**
   - Press `F5` in VS Code (opens new window)
   - Or: `Ctrl+Shift+P` → `Debug: Start Extension Development Host`

3. **Test inline completion:**
   - Open a file (e.g., `page.tsx`)
   - Type code and look for ghost text
   - Press Tab to accept

4. **Check Developer Console:**
   - `Ctrl+Shift+P` → `Developer: Toggle Developer Tools`
   - Click "Console" tab
   - Look for `[completion]` messages

---

## Quick Test Commands

### Test Backend Only:
```powershell
python test_completion_automated.py
```

### Test Simple Case:
```powershell
python test_completion.py
```

### Test Manual in VS Code:
1. Compile extension: `cd vscode-extension && npm run compile`
2. Reload VS Code window
3. Open file and type code
4. Watch for ghost text

---

## What Each Test Does

### `test_completion_automated.py`
**Comprehensive automated test suite:**
- Tests multiple scenarios
- Tests error cases
- Tests performance
- Validates responses

**Use when:** You want to verify backend is working

### `test_completion.py`
**Simple endpoint test:**
- Quick test of one scenario
- Shows completion output
- Good for debugging

**Use when:** You want to quickly test a specific case

### Manual VS Code Testing
**Tests actual user experience:**
- Tests ghost text appearance
- Tests Tab key acceptance
- Tests extension integration
- Tests real-world usage

**Use when:** Backend works, testing full experience

---

## Testing Checklist

### Backend Testing (Automated):
- [ ] Run `python test_completion_automated.py`
- [ ] All tests pass
- [ ] Server health check passes
- [ ] Completions are generated
- [ ] Error handling works
- [ ] Performance is acceptable (<10s)

### Extension Testing (Manual):
- [ ] Extension compiles (`npm run compile`)
- [ ] Extension loads (check console)
- [ ] Backend server is running
- [ ] Repository is indexed (optional)
- [ ] Ghost text appears when typing
- [ ] Tab key accepts completion
- [ ] Multiple completions work
- [ ] Different file types work

---

## Debugging Tips

### If Automated Tests Fail:

1. **Check server is running:**
   ```powershell
   curl http://127.0.0.1:5050/health
   ```

2. **Check server logs:**
   - Look at terminal where server is running
   - Check for error messages

3. **Test manually with curl:**
   ```powershell
   curl -X POST http://127.0.0.1:5050/completion `
     -H "Content-Type: application/json" `
     -d '{"file_path":"test.py","file_content":"def test():","cursor_line":1,"cursor_column":10}'
   ```

### If Manual Tests Fail (No Ghost Text):

1. **Check extension console:**
   - Developer Tools → Console tab
   - Look for errors

2. **Check extension is loaded:**
   - `Ctrl+Shift+P` → Type "Code Assistant"
   - Commands should appear

3. **Check backend is accessible:**
   - Extension needs to reach `http://127.0.0.1:5050`
   - Test in browser: `http://127.0.0.1:5050/health`

4. **Check repository:**
   - Index repository if needed
   - Or set `repo_dir` to None in test

---

## Summary

**✅ Automated Testing:**
- Use for backend endpoint validation
- Run: `python test_completion_automated.py`
- Tests API functionality
- Fast and repeatable

**⚠️ Manual Testing:**
- Required for VS Code extension
- Tests user experience
- Tests UI integration
- Necessary for final validation

**Best Practice:**
1. First: Run automated tests (verify backend)
2. Then: Test manually in VS Code (verify extension)

---

**Note:** While we can't fully automate VS Code extension testing (it requires the VS Code UI), we can thoroughly test the backend endpoint, which is the core functionality. The extension just needs to call the endpoint correctly, which can be verified manually.

