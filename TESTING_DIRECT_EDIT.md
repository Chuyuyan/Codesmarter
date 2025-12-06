# Testing Direct Code Editing in VS Code

## Issue: Command Not Showing in Command Palette

If "Edit Selection with AI" doesn't appear in the command palette, follow these steps:

## Steps to Test the Extension

### 1. Reload VS Code Extension Development Host

After compiling the extension, you need to reload the Extension Development Host window:

1. In the Extension Development Host window (where you're testing the extension)
2. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
3. Type "Reload Window" or "Developer: Reload Window"
4. Press Enter

OR:

1. Look for the green refresh button at the top of the Extension Development Host window
2. Click it to reload the window

### 2. Make Sure You Have Code Selected

The command appears in the command palette **only when you have code selected**:

1. Open a file (e.g., `test.py` or any code file)
2. **Select some code** (highlight text with mouse or Shift+Arrow keys)
3. Press `Ctrl+Shift+P`
4. Type "Edit Selection with AI"
5. The command should appear

### 3. Using Context Menu (Right-Click)

After reloading, you can also use the context menu:

1. Open a file
2. **Select some code**
3. **Right-click** on the selected code
4. Look for "Edit Selection with AI" in the context menu

### 4. Verify Extension is Loaded

Check if the extension is activated:

1. Press `Ctrl+Shift+P`
2. Type "Developer: Show Running Extensions"
3. Look for "Code Assistant" or "code-analysis-assistant"
4. Make sure it shows as "Active"

### 5. Check Extension Output

Check for any errors:

1. Press `Ctrl+Shift+P`
2. Type "View: Show Output"
3. In the Output dropdown, select "Code Assistant" or "Extension Host"
4. Look for any error messages

### 6. Verify Backend Server is Running

Make sure the Flask backend server is running:

1. Open a terminal
2. Run: `python -m backend.app`
3. You should see: `Running on http://127.0.0.1:5050`

## Common Issues

### Command Not Appearing
- **Solution**: Make sure you have code selected in the editor
- **Solution**: Reload the Extension Development Host window
- **Solution**: Check that `package.json` has the command registered

### Command Appears But Doesn't Work
- **Solution**: Check backend server is running (`http://127.0.0.1:5050`)
- **Solution**: Check Developer Console for errors (`Ctrl+Shift+P` → "Developer: Toggle Developer Tools")

### Extension Not Activating
- **Solution**: Check `package.json` has `"activationEvents": ["*"]` for immediate activation
- **Solution**: Reload the Extension Development Host window

## Quick Test Steps

1. ✅ Compile extension: `cd vscode-extension && npm run compile`
2. ✅ Reload Extension Development Host window
3. ✅ Open a code file (e.g., `test.py`)
4. ✅ Select some code
5. ✅ Press `Ctrl+Shift+P`
6. ✅ Type "Edit Selection with AI"
7. ✅ Enter instruction (e.g., "Add error handling")
8. ✅ Wait for AI processing
9. ✅ Click "Apply Directly" to apply the edit

## Alternative: Use Context Menu

1. Select code
2. Right-click on selected code
3. Click "Edit Selection with AI"
4. Enter instruction
5. Apply edit

