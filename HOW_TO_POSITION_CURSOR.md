# How to Position Cursor After 'if' Keyword

## ✅ Simple Steps

### Method 1: Using Mouse (Easiest)

1. **Find line 22** in your `page.tsx` file
   - Look at the left side where line numbers are shown
   - Find line 22 (should show `if` keyword)

2. **Click after the 'if' keyword**
   - Click your mouse right after the letters "if"
   - You should see a blinking cursor appear after "if"

3. **Verify cursor position**
   - The cursor should be blinking after "if"
   - Status bar (bottom) should show: `Ln 22, Col 3` (or similar)

---

### Method 2: Using Keyboard (Faster)

1. **Press `Ctrl+G`** (Go to Line)
   - Or press `Ctrl+P` then type `:22`
   - This jumps directly to line 22

2. **Press `End` key**
   - This moves cursor to end of line
   - Should be after "if"

3. **Or press `→` (Right Arrow)**
   - Move cursor right until after "if"
   - Should be at column 3 (after "if")

---

### Method 3: Using Go to Line

1. **Press `Ctrl+G`** (Go to Line)
   - A prompt appears at top: "Go to Line:Column:"
   
2. **Type `22:3`** and press Enter
   - `22` = line number
   - `3` = column (after "if")
   - Cursor jumps exactly there

---

## 📍 Visual Guide

### Your Code Should Look Like:

```typescript
// Line 21: //have to do a test code
// Line 22: if█
//          ^
//          cursor here
```

**Where `█` = blinking cursor**

---

## ✅ Quick Steps (Copy-Paste):

1. **Press `Ctrl+G`**
2. **Type `22:3`**
3. **Press Enter**
4. **Cursor is now after "if"!**

---

## 🎯 What to Do Next

After positioning cursor:

1. **Type a space** OR press Enter
2. **Wait 1-2 seconds**
3. **Look for ghost text** after cursor
4. **Press Tab** to accept (if ghost text appears)

---

## 💡 Tips

### Check Cursor Position:
- **Status bar** (bottom of VS Code) shows: `Ln 22, Col 3`
- This means: Line 22, Column 3 (after "if")

### If Cursor is Wrong:
- **Click with mouse** where you want cursor
- **Or use arrow keys** (`←` `→` `↑` `↓`) to move

### Multiple Ways:
- Mouse click ✅ (easiest)
- `Ctrl+G` then `22:3` ✅ (fastest)
- Arrow keys ✅ (precise)

---

## 📋 Step-by-Step Visual

1. **Find line 22:**
   ```
   21  //have to do a test code
   22  if
   23  }
   ```

2. **Position cursor:**
   ```
   22  if█  ← cursor here
   ```

3. **Type space:**
   ```
   22  if █  ← cursor moved, wait for ghost text
   ```

4. **Ghost text appears:**
   ```
   22  if (ghost text here)█
   ```

5. **Press Tab:**
   ```
   22  if (actual code inserted)█
   ```

---

**Try it now: Press `Ctrl+G`, type `22:3`, press Enter!** 🚀

