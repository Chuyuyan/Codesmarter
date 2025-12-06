# 🚀 Quick Start Guide

## Step 1: Start Backend Server

**Open a NEW PowerShell terminal** (keep this running):

```powershell
cd C:\Users\57811\smartcursor
.\.venv\Scripts\Activate.ps1
python -m backend.app
```

You should see:
```
 * Running on http://127.0.0.1:5050
```

**Keep this terminal open!**

---

## Step 2: Launch Extension in VS Code

**In VS Code** (opened in `vscode-extension` folder):

1. **Press `F5`** (or menu: Run > Start Debugging)

2. **Select "Run Extension"** from the dropdown
   - If you see "Select debugger", choose "Run Extension"
   - Press Enter

3. **Wait for new window to open**
   - A new VS Code window will open
   - Title: **[Extension Development Host]**
   - You'll see notification: "Code Assistant extension activated!"

---

## Step 3: Test the Extension

**In the NEW VS Code window** (Extension Development Host):

1. **Open a workspace folder:**
   - File > Open Folder
   - Select `C:\Users\57811\my-portfolio` (or any code folder)
   - Click "Select Folder"

2. **Press `Ctrl+Shift+P`** (Command Palette)

3. **Type:** `Code Assistant`

4. **You should see 3 commands:**
   - ✅ Code Assistant: Index Repository
   - ✅ Code Assistant: Ask Question About Code
   - ✅ Code Assistant: Open Chat Panel

5. **Select:** `Code Assistant: Open Chat Panel`
   - Chat panel should open on the side!

6. **Ask a question:**
   - Type a question in the chat
   - Click "Send Question"
   - See the answer appear!

---

## Troubleshooting

**"Run Extension" doesn't appear:**
- Make sure VS Code is opened in `vscode-extension` folder
- Check `.vscode/launch.json` exists

**Extension doesn't activate:**
- Check Output panel (View > Output)
- Select "Log (Extension Host)" from dropdown
- Look for "Code Assistant extension is now active!" message

**Can't connect to server:**
- Make sure backend server is running in a separate terminal
- Check it's on `http://127.0.0.1:5050`
- Test in browser: `http://127.0.0.1:5050/health`

---

## Quick Checklist

- [ ] Backend server running (http://127.0.0.1:5050)
- [ ] VS Code opened in `vscode-extension` folder
- [ ] Pressed F5 and selected "Run Extension"
- [ ] New window opened with "[Extension Development Host]"
- [ ] Notification appeared: "Code Assistant extension activated!"
- [ ] Opened a workspace folder in the new window
- [ ] Pressed Ctrl+Shift+P and typed "Code Assistant"
- [ ] All 3 commands appeared
- [ ] Chat panel opened successfully!

---

**You're ready! Start with Step 1 above.** 🎉

