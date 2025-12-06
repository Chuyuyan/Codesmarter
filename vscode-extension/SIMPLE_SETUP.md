# Simple Setup - How to Run Extension

## The Easiest Way

### Step 1: Open VS Code in the Extension Folder

**IMPORTANT:** Open VS Code in the `vscode-extension` folder, NOT the project root!

```powershell
cd C:\Users\57811\smartcursor\vscode-extension
code .
```

Or manually:
1. Open VS Code
2. File > Open Folder
3. Navigate to `C:\Users\57811\smartcursor\vscode-extension`
4. Click "Select Folder"

### Step 2: Start Backend Server (Separate Terminal)

**In a NEW PowerShell terminal** (keep this running):
```powershell
cd C:\Users\57811\smartcursor
.\.venv\Scripts\Activate.ps1
python -m backend.app
```

### Step 3: Press F5 in VS Code

1. In VS Code (opened in `vscode-extension` folder)
2. Press **F5**
3. **"Run Extension"** should appear in the debug dropdown
4. Select it or press Enter
5. A new VS Code window will open: **[Extension Development Host]**

### Step 4: Test the Extension

In the **NEW** window that opened:

1. **Open a workspace folder:**
   - File > Open Folder
   - Select `C:\Users\57811\my-portfolio` (or any code folder)

2. **Press Ctrl+Shift+P**

3. **Type:** `Code Assistant`
   - You should see:
     - Code Assistant: Index Repository
     - Code Assistant: Ask Question About Code
     - Code Assistant: Open Chat Panel

4. **Select:** `Code Assistant: Open Chat Panel`
   - Chat panel should open on the side!

## Troubleshooting

**If "Run Extension" doesn't appear:**
1. Make sure you opened VS Code in the `vscode-extension` folder
2. Check if `.vscode/launch.json` exists in `vscode-extension` folder
3. Reload VS Code: `Ctrl+Shift+P` → `Developer: Reload Window`

**If extension doesn't activate:**
1. Check the Output panel (View > Output)
2. Select "Log (Extension Host)" from dropdown
3. Look for "Code Assistant extension is now active!" message

