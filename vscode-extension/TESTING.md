# Testing the VS Code Extension

## Step-by-Step Guide

### Step 1: Make sure backend server is running

**Open a NEW PowerShell terminal** (keep this open):
```powershell
cd C:\Users\57811\smartcursor
.\.venv\Scripts\Activate.ps1
python -m backend.app
```

Keep this terminal running - the server must be active!

### Step 2: Open VS Code with the extension

1. **Open VS Code** in the extension directory:
   ```powershell
   code vscode-extension
   ```
   Or manually:
   - Open VS Code
   - File > Open Folder
   - Select `C:\Users\57811\smartcursor\vscode-extension`

### Step 3: Launch Extension Development Host

1. In VS Code, press **`F5`** (or go to menu: Run > Start Debugging)
2. A **NEW VS Code window** will open - this is the "Extension Development Host"
3. The title bar will say: **[Extension Development Host]**

### Step 4: Test the Extension

In the NEW VS Code window that opened:

1. **Open a workspace folder**:
   - File > Open Folder
   - Select `C:\Users\57811\my-portfolio` (or any code folder)

2. **Index the repository**:
   - Press **`Ctrl+Shift+P`** (Command Palette)
   - Type: `Code Assistant: Index Repository`
   - Press Enter
   - Click "Yes" when prompted
   - Wait for indexing to complete (status bar will show progress)

3. **Open Chat Panel**:
   - Press **`Ctrl+Shift+P`**
   - Type: `Code Assistant: Open Chat Panel`
   - Press Enter
   - A chat panel will open on the side

4. **Ask a question**:
   - Type a question in the chat panel
   - Click "Send Question" or press Ctrl+Enter
   - See the answer appear!

## Troubleshooting

**Extension window doesn't open when pressing F5:**
- Check the "Run and Debug" panel in VS Code for errors
- Make sure TypeScript compiled successfully

**"Cannot connect to server" error:**
- Make sure backend server is running in separate terminal
- Check server is on http://127.0.0.1:5050
- Test with: `curl http://127.0.0.1:5050/health` or browser

**No commands appear in Command Palette:**
- Make sure you're in the Extension Development Host window (new window)
- Extension might not have activated - check the output panel

## Quick Test Checklist

- [ ] Backend server is running (http://127.0.0.1:5050)
- [ ] VS Code opened in vscode-extension folder
- [ ] Pressed F5 and new window opened
- [ ] Opened a workspace folder in the new window
- [ ] Command Palette shows "Code Assistant" commands
- [ ] Index Repository works
- [ ] Chat Panel opens
- [ ] Questions get answered

