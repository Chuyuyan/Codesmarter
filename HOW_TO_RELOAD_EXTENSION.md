# How to Reload Extension Development Host

## Method 1: Using Command Palette (Easiest) ✅

1. **In the Extension Development Host window** (the second VS Code window that opened when you pressed F5)
2. Press **`Ctrl+Shift+P`** (or `Cmd+Shift+P` on Mac)
3. Type: **`reload window`**
4. Select: **`Developer: Reload Window`**
5. Press **Enter**

---

## Method 2: Using the Reload Button (Visual) ✅

1. Look at the **top** of the Extension Development Host window
2. You should see a **green circular arrow icon** (↻) or **refresh button**
3. **Click on it** to reload the window

**Note**: The reload button appears at the top of the Extension Development Host window, near the title bar.

---

## Method 3: Close and Reopen

1. **Close** the Extension Development Host window
2. **In the original VS Code window** (where you ran `F5` to debug the extension)
3. Press **`F5`** again to launch Extension Development Host
4. A new Extension Development Host window will open with the latest code

---

## After Reloading

After reloading, make sure you:

1. ✅ **Open a code file** (e.g., `test.py`)
2. ✅ **Select some code** (highlight with mouse or `Shift+Arrow` keys)
3. ✅ **Right-click** → "Edit Selection with AI" OR
4. ✅ **Press `Ctrl+Shift+P`** → Type "Edit Selection with AI"

---

## Quick Test After Reload

1. Open any `.py`, `.js`, `.ts` file (or any code file)
2. Type some code:
   ```python
   def test():
       return 5
   ```
3. **Select** the code (highlight it)
4. **Right-click** → "Edit Selection with AI"
5. Enter instruction: "Add error handling"
6. Click "Apply Directly" when ready

---

## Troubleshooting

### Still not showing?

1. **Check if extension is active**:
   - Press `Ctrl+Shift+P`
   - Type "Show Running Extensions"
   - Look for "Code Assistant" - should show as "Active"

2. **Check Developer Console**:
   - Press `Ctrl+Shift+P`
   - Type "Toggle Developer Tools"
   - Look for errors in the Console tab

3. **Make sure code is selected**:
   - The command only appears when you have code selected
   - Try selecting different amounts of code (few lines, multiple lines)

4. **Check backend server is running**:
   - Open terminal
   - Run: `python -m backend.app`
   - Should see: `Running on http://127.0.0.1:5050`

---

**That's it! Reload and test!** 🚀

