# Streaming Functionality Testing Guide

This guide explains how to test the newly implemented streaming features with real-time progress indicators.

## Prerequisites

1. **Backend server must be running**
   ```powershell
   python -m backend.app
   ```
   You should see: `* Running on http://127.0.0.1:5050`

2. **VS Code Extension compiled**
   ```powershell
   cd vscode-extension
   npm run compile
   ```
   Make sure there are no TypeScript errors.

3. **Extension reloaded in VS Code**
   - Press `F5` to open Extension Development Host (if not already open)
   - Or reload the window: `Ctrl+Shift+P` → "Developer: Reload Window"

---

## Test 1: Generate Tests (Streaming)

### Steps:
1. Open a Python file in VS Code (e.g., `test.py`)
2. Select a function or class to test
3. **Right-click** on the selection → **"Generate Tests for Selection"**
   - OR use Command Palette: `Ctrl+Shift+P` → "Generate Tests for Selection"
   - OR use the keyboard shortcut (if configured)

### What You Should See:

#### Progress Indicator (Notification):
- **0%**: "Analyzing code... (0%)"
- **10%**: "Searching codebase context... (10%)"
- **30%**: "Streaming test code... (30%)"
- **30-90%**: "Generating tests... (X%) - Y chars" (updates in real-time as chunks arrive)
- **95%**: "Finalizing... (95%)"
- **100%**: "Done! (100%)"

#### Console Logs (Developer Console - `Ctrl+Shift+I`):
```
[generateTests] Starting streaming request to: http://127.0.0.1:5050/generate_tests
[generateTests] Stream started
[generateTests] Stream completed, metadata: {...}
[generateTests] Creating document with X chars
[generateTests] Document shown successfully
```

#### Final Result:
- **New document** opens in a split view showing generated test code
- **Notification**: "✅ Tests generated! (X lines)"
- Test code should be complete and properly formatted

---

## Test 2: Generate Documentation (Streaming)

### Steps:
1. Open a code file (Python, TypeScript, etc.)
2. Select a function, class, or code block
3. **Right-click** → **"Generate Documentation for Selection"**
   - OR Command Palette: `Ctrl+Shift+P` → "Generate Documentation for Selection"

### What You Should See:

#### Progress Indicator:
- **0%**: "Analyzing code... (10%)"
- **20%**: "Searching codebase context... (20%)"
- **30%**: "Streaming documentation... (30%)"
- **30-90%**: "Generating documentation... (X%) - Y chars" (real-time updates)
- **95%**: "Finalizing... (95%)"
- **100%**: "Done! (100%)"

#### Console Logs:
```
[generateDocs] Stream started
[generateDocs] Stream completed, metadata: {...}
```

#### Final Result:
- **New document** opens showing generated documentation (docstring/README/etc.)
- **Notification**: "✅ Documentation generated! (X lines)"
- Documentation should be properly formatted (Google style for Python, JSDoc for JS/TS)

---

## Test 3: Edit Selection with AI (Streaming)

### Steps:
1. Select some code in your editor
2. Press **`Ctrl+Alt+E`** (or `Ctrl+K` then `Ctrl+E`)
   - OR **Right-click** → **"Edit Selection with AI"**
3. Enter an edit instruction (e.g., "Add error handling", "Optimize this function")
4. Press Enter

### What You Should See:

#### Progress Indicator:
- **0%**: "Analyzing code... (10%)"
- **20%**: "Preparing edit request... (20%)"
- **30%**: "Streaming edited code... (30%)"
- **30-90%**: "AI is editing your code... (X%) - Y chars" (real-time updates)
- **95%**: "Finalizing... (95%)"
- **100%**: "Done! (100%)"

#### Console Logs:
```
[edit] Stream started
[edit] Stream completed, metadata: {...}
```

#### Final Result:
- **Dialog**: "AI has generated an edit. What would you like to do?"
  - Options: "Preview Diff", "Apply Directly", "Cancel"
- If you choose **"Preview Diff"**: Side-by-side diff view opens
- If you choose **"Apply Directly"**: Code is immediately replaced

---

## Test 4: Refactor Selection (Streaming)

### Steps:
1. Open a file with code to refactor
2. Select the code (function, class, or code block)
3. **Right-click** → **"Refactor Selection"**
   - OR Command Palette: `Ctrl+Shift+P` → "Refactor Selection"

### What You Should See:

#### Progress Indicator:
- **0%**: "Analyzing code... (10%)"
- **20%**: "Searching codebase... (20%)"
- **30%**: "Streaming refactoring suggestions... (30%)"
- **30-90%**: "Analyzing code with AI... (X%) - Y chars" (real-time updates)
- **95%**: "Finalizing... (95%)"
- **100%**: "Done! (100%)"

#### Console Logs:
```
[refactor] Stream started
[refactor] Stream completed, metadata: {...}
```

#### Final Result:
- **Webview panel** opens showing refactoring suggestions
- Suggestions are formatted as markdown with:
  - Before/After code comparisons
  - Benefits of each refactoring
  - Explanations
- **Notification**: "✅ Refactoring suggestions generated! (X lines)"

---

## Key Indicators of Success ✅

### 1. **Real-Time Progress Updates**
- Progress percentage should **increase smoothly** as chunks arrive
- Character count (`Y chars`) should **increment** with each chunk
- Progress should **not jump** from 30% to 90% instantly (should be gradual)

### 2. **Streaming Behavior**
- Progress updates should happen **multiple times** during generation
- You should see progress at: 35%, 42%, 55%, 68%, 78%, 87%, etc.
- **Not** just at the start and end

### 3. **Console Logs**
- `[X] Stream started` should appear immediately
- `[X] Stream completed, metadata: {...}` should appear at the end
- No errors in between

### 4. **Final Results**
- Content should be **complete** (not truncated)
- Code/documentation should be **properly formatted**
- All metadata should be present (lines, language, etc.)

---

## Troubleshooting

### Issue: Progress stays at 30% and doesn't move
**Cause**: Streaming not working, or backend not returning chunks
**Solution**: 
- Check backend logs for errors
- Verify backend server is running
- Check console logs for streaming errors

### Issue: Progress jumps from 30% to 100% instantly
**Cause**: Using non-streaming endpoint or streaming not enabled
**Solution**:
- Verify `stream: true` is in the request payload (check console logs)
- Ensure backend streaming endpoints are working (test with `test_refactor_streaming.py`)

### Issue: "Cannot connect to backend server"
**Cause**: Backend server not running
**Solution**:
```powershell
python -m backend.app
```

### Issue: Empty results or no output
**Cause**: Backend returned empty response or error
**Solution**:
- Check backend server logs
- Check VS Code Developer Console for error messages
- Verify the selected code is valid

### Issue: TypeScript compilation errors
**Cause**: Syntax errors in extension code
**Solution**:
```powershell
cd vscode-extension
npm run compile
```
Fix any errors shown.

---

## Expected Timeline

- **Small code snippets** (< 50 lines): 10-30 seconds
- **Medium code** (50-200 lines): 30-90 seconds
- **Large code** (> 200 lines): 1-3 minutes

Progress should update **every 1-3 seconds** during streaming.

---

## Developer Console Access

To see detailed logs:
1. Open VS Code Developer Tools: `Ctrl+Shift+I` (or `Cmd+Option+I` on Mac)
2. Go to **Console** tab
3. Filter by `[generateTests]`, `[generateDocs]`, `[edit]`, or `[refactor]`

---

## Success Criteria ✅

1. ✅ Progress indicator shows **real-time updates** (not just start/end)
2. ✅ Progress percentage **increases gradually** (30% → 40% → 50% → ... → 90%)
3. ✅ Character count **increments** during streaming
4. ✅ Final result is **complete** and **correct**
5. ✅ No errors in console
6. ✅ All operations **cancelable** (click Cancel button)

---

## Next Steps After Testing

If all tests pass:
- ✅ Streaming functionality is working correctly
- ✅ Real-time progress indicators are functional
- ✅ User experience is significantly improved

If tests fail:
- Check backend server logs
- Check VS Code Developer Console
- Verify backend streaming endpoints work (use test scripts)
- Report specific errors and we can fix them

