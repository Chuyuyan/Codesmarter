# Troubleshooting Guide

## Common Errors and Solutions

### Error: `connect ECONNREFUSED 127.0.0.1:5050`

**Problem:** Backend server is not running.

**Solution:**
1. Open a NEW PowerShell terminal (separate from VS Code)
2. Run these commands:
   ```powershell
   cd C:\Users\57811\smartcursor
   .\.venv\Scripts\Activate.ps1
   python -m backend.app
   ```
3. You should see:
   ```
    * Running on http://127.0.0.1:5050
   ```
4. **Keep this terminal running!**
5. Go back to VS Code and try asking again

**Remember:** The backend server must be running at all times when using the extension!

---

### Error: `repo_dir not found: c:Users/811my-portfolio`

**Problem:** Path formatting issue (should be fixed now).

**Solution:**
1. Reload the Extension Development Host window:
   - Press `Ctrl+Shift+P`
   - Type: `Developer: Reload Window`
   - Press Enter
2. Reopen the chat panel
3. Try asking again

---

### Commands Not Showing in Command Palette

**Problem:** Extension not activated or commands not registered.

**Solution:**
1. Make sure VS Code is opened in `vscode-extension` folder
2. Check Output panel for errors:
   - View > Output
   - Select "Log (Extension Host)" from dropdown
   - Look for "Code Assistant extension is now active!" message
3. Reload the Extension Development Host window
4. Press F5 again in the main VS Code window

---

### Extension Not Activating

**Problem:** Extension fails to activate.

**Check:**
1. Backend server is running
2. VS Code is opened in `vscode-extension` folder
3. TypeScript compiled successfully (`npm run compile`)

**Solution:**
1. Check Output panel (View > Output > "Log (Extension Host)")
2. Look for error messages
3. Recompile: `npm run compile`
4. Reload Extension Development Host window

---

### Can't Connect to Server After Starting

**Problem:** Server started but extension still can't connect.

**Check:**
1. Server is actually running (check terminal)
2. Server is on correct port (5050)
3. Firewall is not blocking

**Solution:**
1. Test server directly in browser: `http://127.0.0.1:5050/health`
2. Should return: `{"ok":true,"port":5050}`
3. If not, restart the server

---

## Quick Checklist

Before asking questions, make sure:

- [ ] Backend server is running (`python -m backend.app`)
- [ ] Server shows: `* Running on http://127.0.0.1:5050`
- [ ] Repository is indexed (`Code Assistant: Index Repository`)
- [ ] Workspace folder is open in VS Code
- [ ] Chat panel is open

---

## Need More Help?

1. Check the Output panel for error messages
2. Check the backend server terminal for errors
3. Make sure all dependencies are installed
4. Try reloading everything:
   - Reload Extension Development Host window
   - Restart backend server
   - Reindex repository

