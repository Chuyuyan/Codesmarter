# Code Analysis Assistant - VS Code Extension

A VS Code extension that integrates with the Code Analysis Assistant backend, providing AI-powered code analysis directly in VS Code - similar to Cursor!

## Features

- 📚 **Index Repository** - Index your workspace for code analysis
- 💬 **Chat Interface** - Ask questions about your codebase in a sidebar panel
- 🔍 **Code Citations** - See exactly where answers come from
- 🎯 **Analysis Types** - Explain, Refactor, Debug, Optimize

## Prerequisites

1. **Backend Server Must Be Running**
   - Start the backend server first: `python -m backend.app`
   - Server should run on `http://127.0.0.1:5050`

2. **VS Code** version 1.80.0 or higher

## Installation

### Development Mode

1. Install dependencies:
   ```bash
   cd vscode-extension
   npm install
   ```

2. Compile TypeScript:
   ```bash
   npm run compile
   ```

3. Press F5 in VS Code to launch extension development host

### Production Build

1. Install vsce (VS Code Extension Manager):
   ```bash
   npm install -g @vscode/vsce
   ```

2. Package the extension:
   ```bash
   cd vscode-extension
   vsce package
   ```

3. Install the `.vsix` file in VS Code:
   - Open VS Code
   - Go to Extensions
   - Click "..." menu
   - Select "Install from VSIX..."
   - Choose the generated `.vsix` file

## Usage

1. **Open a workspace folder** in VS Code

2. **Index Repository**:
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
   - Type "Code Assistant: Index Repository"
   - Select the command
   - Wait for indexing to complete

3. **Ask Questions**:
   - Press `Ctrl+Shift+P`
   - Type "Code Assistant: Open Chat Panel"
   - Ask questions about your code in the chat panel

## Commands

- `Code Assistant: Index Repository` - Index current workspace
- `Code Assistant: Ask Question About Code` - Quick chat
- `Code Assistant: Open Chat Panel` - Open chat sidebar

## Configuration

In VS Code settings, you can configure:

- `codeAssistant.serverUrl` - Backend server URL (default: http://127.0.0.1:5050)
- `codeAssistant.defaultRepoPath` - Default repository path

## Troubleshooting

**Extension doesn't connect to server:**
- Make sure backend server is running: `python -m backend.app`
- Check server URL in VS Code settings

**Import errors in extension:**
- Run `npm install` in the `vscode-extension` directory
- Run `npm run compile` to build TypeScript

