# Quick Debug Steps - Extension Not Showing Logs

## If "Log (Extension Host)" is Missing from Output Panel

### ✅ Step 1: Check if Extension is Loaded

**Test Extension Commands:**
1. Press `Ctrl+Shift+P` (Command Palette)
2. Type: `Code Assistant`
3. Do you see these commands?
   - ✅ `Index Repository`
   - ✅ `Open Chat Panel`

**If YES:** Extension is loaded! ✅  
**If NO:** Extension is not loaded ❌

---

### ✅ Step 2: Check Developer Console (Shows All Errors)

1. Press `Ctrl+Shift+P`
2. Type: `Developer: Toggle Developer Tools`
3. Press Enter
4. Click **"Console"** tab
5. Look for:
   - ✅ `Code Assistant extension is now active!` (good!)
   - ❌ Any red error messages (bad!)

**This shows ALL extension activity, even if Output panel doesn't show logs!**

---

### ✅ Step 3: Check Backend Server

**Quick Test:**
Open browser: `http://127.0.0.1:5050/health`

**Should see:** `{"status": "ok"}`

**If error:**
- Server not running
- Start it: `python -m backend.app`

---

### ✅ Step 4: Check Extension Files

1. Go to: `vscode-extension/out/`
2. Should see: `extension.js` file
3. **If missing:** Extension not compiled!

**Compile it:**
```powershell
cd vscode-extension
npm run compile
```

---

### ✅ Step 5: Reload Extension

1. Press `Ctrl+Shift+P`
2. Type: `Developer: Reload Window`
3. Press Enter
4. VS Code window will reload
5. Extension should load

---

### ✅ Step 6: Check Extension Installation

1. Press `Ctrl+Shift+X` (Extensions panel)
2. Search: `Code Analysis Assistant`
3. Check if extension is:
   - ✅ Installed
   - ✅ Enabled
   - ✅ Not disabled

---

### ✅ Step 7: Test Backend Directly (Bypass Extension)

**This tests if backend works, even if extension doesn't:**

```powershell
python test_completion.py
```

**If this works:** Backend is fine ✅ → Issue is with extension  
**If this fails:** Backend issue ❌ → Fix backend first

---

## Quick Checklist

- [ ] Extension commands appear in Command Palette?
- [ ] Developer Console shows extension activation?
- [ ] Backend server running? (`http://127.0.0.1:5050/health`)
- [ ] Extension compiled? (`out/extension.js` exists?)
- [ ] Extension enabled in Extensions panel?
- [ ] VS Code window reloaded after compilation?

---

## Most Likely Issues

### Issue 1: Extension Not Compiled
**Solution:** `cd vscode-extension && npm run compile`

### Issue 2: Extension Not Loaded After Compilation
**Solution:** Reload VS Code window (`Ctrl+Shift+P` → `Developer: Reload Window`)

### Issue 3: Backend Server Not Running
**Solution:** `python -m backend.app`

### Issue 4: Extension Has Errors (Check Developer Console)
**Solution:** Check Console tab in Developer Tools for error messages

---

## Test Inline Completion Without Logs

Even if logs don't appear, you can still test:

1. **Open `page.tsx`**
2. **Position cursor** after a function
3. **Type:** `// TODO: add error handling`
4. **Press Enter** (or type a space)
5. **Wait 1-2 seconds**
6. **Look for grayed-out ghost text**

**If ghost text appears:** It's working! ✅  
**If nothing appears:** Check Developer Console for errors

---

**Remember:** The Developer Console (`Ctrl+Shift+P` → `Developer: Toggle Developer Tools` → Console tab) shows ALL extension activity, even if Output panel doesn't show logs!

