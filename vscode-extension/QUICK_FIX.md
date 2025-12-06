# Quick Fix: Commands Not Showing

## The Issue
If you don't see "Code Assistant: Open Chat Panel" in the Command Palette, the Extension Development Host window needs to reload.

## Solution

### Step 1: Reload the Extension Development Host Window

1. **In the [Extension Development Host] window** (the one that opened when you pressed F5):
   - Press `Ctrl+Shift+P`
   - Type: `Developer: Reload Window`
   - Press Enter
   - The window will reload with the extension

2. **After reload**, press `Ctrl+Shift+P` again
   - Type: `Code Assistant`
   - You should now see all 3 commands:
     - ✅ Code Assistant: Index Repository
     - ✅ Code Assistant: Ask Question About Code
     - ✅ Code Assistant: Open Chat Panel

### Step 2: If Still Not Working

**Close and restart:**
1. Close the [Extension Development Host] window
2. Go back to your main VS Code window (where you pressed F5)
3. Press **F5** again to launch a new Extension Development Host
4. Open a workspace folder in the new window
5. Press `Ctrl+Shift+P` and type `Code Assistant`

### Step 3: Check for Errors

**View Output Logs:**
1. In VS Code main window, go to **View > Output** (or `Ctrl+Shift+U`)
2. In the dropdown at the top right, select **"Log (Extension Host)"**
3. Look for messages like:
   - "Code Assistant extension is now active!"
   - "Code Assistant commands registered:"
4. If you see errors, share them

### Alternative: Search All Commands

1. Press `Ctrl+Shift+P`
2. Type: `@ext:code-analysis-assistant` 
3. This shows all commands from the extension

## Quick Test

After reloading, try this:
1. Press `Ctrl+Shift+P`
2. Type: `Code Assistant: Open Chat Panel`
3. Press Enter
4. The chat panel should open!

