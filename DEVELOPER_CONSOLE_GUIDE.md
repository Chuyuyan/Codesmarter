# How to Use Developer Console for Debugging

## ✅ Developer Tools is Open!

You're currently on the **"Elements"** tab. You need to switch to the **"Console"** tab to see extension logs.

---

## Step-by-Step Instructions

### 1. Switch to Console Tab

**At the top of Developer Tools window, you'll see tabs:**
- Elements ← You're here
- **Console** ← Click this one!
- Sources
- Network
- Performance
- Memory
- Application

**Click on "Console" tab**

---

### 2. What to Look For in Console Tab

#### ✅ Extension Loaded Successfully:
```
Code Assistant extension is now active!
Inline Completion Provider (Tab feature - like Cursor)
```

**If you see these:** Extension is loaded! ✅

#### ✅ Completion Requests (when typing):
```
[completion] Requesting inline completion for page.tsx:45:1
[completion] Generated inline completion (246 chars): ...
```

**If you see these:** Extension is calling backend! ✅

#### ❌ Errors (red text):
```
Error: Cannot find module '...'
Error: ECONNREFUSED http://127.0.0.1:5050
TypeError: ...
```

**If you see these:** There's an issue to fix ❌

---

### 3. Filter Console Messages

**In Console tab, there's a filter box at the top.**

**Type to filter:**
- `completion` - See all completion-related messages
- `Code Assistant` - See extension activation messages
- `error` - See only errors

---

### 4. Test Inline Completion

**While Console tab is open:**

1. **Go back to VS Code editor** (click on editor window)
2. **Open `page.tsx`**
3. **Type after your TODO comment:**
   ```typescript
   // TODO: add error handling
   [Press Enter or Space here]
   ```
4. **Watch Console tab** - You should see:
   ```
   [completion] Requesting inline completion for page.tsx:45:1
   ```
5. **If you see the message:** Extension is working! ✅
6. **If you don't see message:** Extension not triggering

---

### 5. Common Issues & Solutions

#### Issue: "Code Assistant extension is now active!" not showing
**Solution:** Extension not loaded
- Reload VS Code: `Ctrl+Shift+P` → `Developer: Reload Window`
- Or check if extension is enabled

#### Issue: Error: "Cannot find module"
**Solution:** Extension not compiled
```powershell
cd vscode-extension
npm run compile
```

#### Issue: Error: "ECONNREFUSED" or connection errors
**Solution:** Backend server not running
```powershell
python -m backend.app
```

#### Issue: No completion messages when typing
**Solution:** 
- Make sure you're actually **typing** (not just positioning cursor)
- Wait 1-2 seconds after typing
- Check if repository is indexed

---

### 6. Console Tab Tips

- **Clear console:** Click the 🚫 icon (or `Ctrl+L`)
- **Filter messages:** Type in filter box at top
- **Copy messages:** Right-click on message → Copy
- **Focus console:** Click on Console tab

---

## Quick Checklist

- [ ] Clicked "Console" tab (not Elements)?
- [ ] See "Code Assistant extension is now active!"?
- [ ] See `[completion]` messages when typing?
- [ ] Any red error messages?
- [ ] Backend server running?
- [ ] Extension compiled?

---

**Remember:** The Console tab shows ALL extension activity and errors. This is the best way to debug!

