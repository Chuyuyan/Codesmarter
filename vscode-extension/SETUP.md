# VS Code Extension Setup Guide

## Quick Start

### Step 1: Install Node.js Dependencies

```bash
cd vscode-extension
npm install
```

### Step 2: Compile TypeScript

```bash
npm run compile
```

### Step 3: Test the Extension

1. Open VS Code in this workspace
2. Press `F5` (or go to Run > Start Debugging)
3. A new VS Code window will open with the extension loaded
4. In the new window:
   - Open a workspace folder
   - Press `Ctrl+Shift+P` 
   - Type "Code Assistant: Index Repository"
   - Then "Code Assistant: Open Chat Panel"

### Step 4: Install Extension (Optional - for regular use)

```bash
# Install vsce globally (if not already installed)
npm install -g @vscode/vsce

# Package the extension
vsce package

# Install in VS Code:
# 1. Open VS Code
# 2. Go to Extensions (Ctrl+Shift+X)
# 3. Click "..." menu
# 4. Select "Install from VSIX..."
# 5. Choose the generated .vsix file
```

## Prerequisites

1. **Backend server must be running** on http://127.0.0.1:5050
   - In a separate terminal: `python -m backend.app`

2. **Node.js** installed
   - Check: `node --version`
   - If not installed: Download from https://nodejs.org/

## Features in VS Code

- **Command Palette Commands**:
  - `Code Assistant: Index Repository` - Index current workspace
  - `Code Assistant: Ask Question About Code` - Quick question
  - `Code Assistant: Open Chat Panel` - Full chat interface

- **Chat Panel**:
  - Sidebar panel for conversations
  - Analysis type selector
  - Code citations display
  - Markdown-formatted answers

## Troubleshooting

**"Cannot find module 'axios'"**:
```bash
cd vscode-extension
npm install
```

**TypeScript errors**:
```bash
npm run compile
```

**Extension doesn't connect**:
- Check backend server is running
- Verify URL in VS Code settings: `codeAssistant.serverUrl`

