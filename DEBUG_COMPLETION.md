# Debugging Inline Completion - Why Nothing Appears

## Common Issues

### 1. **Cursor Position vs. Typing**
- ❌ Just positioning cursor won't trigger completions
- ✅ You need to **actually type** something
- ✅ Type a few characters, then wait 1-2 seconds

### 2. **Extension Not Loaded**
Check if extension is active:
1. Press `Ctrl+Shift+U` (Output panel)
2. Select **"Log (Extension Host)"**
3. Look for: `Code Assistant extension is now active!`
4. Look for: `Inline Completion Provider (Tab feature - like Cursor)`

If you don't see these, the extension isn't loaded. Try:
- Reload VS Code window (`Ctrl+R`)
- Or compile extension: `cd vscode-extension && npm run compile`

### 3. **Backend Server Not Running**
Check if backend is running:
```powershell
curl http://127.0.0.1:5050/health
```
Or test in browser: `http://127.0.0.1:5050/health`

Should return: `{"status": "ok"}`

If not running, start it:
```powershell
python -m backend.app
```

### 4. **Repository Not Indexed**
Completions work better if repository is indexed:
1. Press `Ctrl+Shift+P`
2. Type: `Code Assistant: Index Repository`
3. Select it and confirm

### 5. **Check Console Logs**
In **Output panel** → **"Log (Extension Host)"**, look for:
```
[completion] Requesting inline completion for page.tsx:45:1
```

**If you see this:** Extension is calling backend (good!)
**If you don't see this:** Extension might not be triggering

### 6. **Try This Test**
In `page.tsx`, try this:

```typescript
function testFunction() {
    // TODO: add
    // <-- Position cursor here, then TYPE a space or newline
    // After typing, wait 1-2 seconds
    // Ghost text should appear
}
```

**Key:** You must TYPE something, not just position cursor!

### 7. **Configuration Check**
1. Press `Ctrl+,` (Settings)
2. Search: `codeAssistant.enableInlineCompletion`
3. Should be **checked/enabled** (true)

---

## Quick Debug Checklist

- [ ] Extension compiled? (`cd vscode-extension && npm run compile`)
- [ ] VS Code window reloaded? (`Ctrl+R`)
- [ ] Backend server running? (`http://127.0.0.1:5050/health`)
- [ ] Repository indexed? (Run: Code Assistant: Index Repository)
- [ ] Actually typing (not just positioning cursor)?
- [ ] Waiting 1-2 seconds after typing?
- [ ] Check console logs for `[completion]` messages?

---

## What Should Happen

1. You **type code** → e.g., `const handleSubmit = () => {`
2. You **type some more** → e.g., press Enter, type a space
3. **Wait 1-2 seconds** → (API call happening)
4. **Ghost text appears** → Grayed-out suggestion
5. **Press Tab** → Accept suggestion

The key is that you need to **actively type**, not just position the cursor!

