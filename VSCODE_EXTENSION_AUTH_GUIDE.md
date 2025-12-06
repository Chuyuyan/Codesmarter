# VS Code Extension Authentication Guide

## 🎯 Key Difference: VS Code Extensions vs Web Apps

**VS Code Extensions DON'T need a full login page like web apps!**

### Web Application Authentication
- Full HTML/CSS login page
- Form inputs with styling
- Redirect after login
- Session management in browser

### VS Code Extension Authentication
- **Simpler patterns** using VS Code's native UI
- **No HTML pages needed**
- Uses VS Code's built-in UI components

## ✅ Recommended Authentication Patterns for VS Code Extensions

### 1. **Input Box Prompts** (Simplest)
```typescript
// Login command
async function login() {
    const username = await vscode.window.showInputBox({
        prompt: 'Enter your username or email',
        placeHolder: 'username@example.com'
    });
    
    const password = await vscode.window.showInputBox({
        prompt: 'Enter your password',
        password: true  // Hides input
    });
    
    // Call API
    const response = await api.login(username, password);
    
    // Store token securely
    await context.secrets.store('authToken', response.token);
}
```

### 2. **Settings/Configuration** (For API Keys)
```json
// package.json
"contributes": {
    "configuration": {
        "properties": {
            "smartcursor.apiKey": {
                "type": "string",
                "default": "",
                "description": "Your API key"
            }
        }
    }
}
```

```typescript
// Read from settings
const config = vscode.workspace.getConfiguration('smartcursor');
const apiKey = config.get<string>('apiKey');
```

### 3. **Status Bar with Login Command**
```typescript
// Show login status in status bar
const statusBar = vscode.window.createStatusBarItem(
    vscode.StatusBarAlignment.Right, 100
);

statusBar.text = "$(sign-in) Login";
statusBar.command = 'smartcursor.login';
statusBar.show();

// After login
statusBar.text = "$(account) Logged in as username";
statusBar.command = 'smartcursor.logout';
```

### 4. **Webview Panel** (For Complex UIs)
Only use if you need a complex authentication flow (OAuth, etc.)

```typescript
const panel = vscode.window.createWebviewPanel(
    'auth',
    'Login',
    vscode.ViewColumn.One,
    { enableScripts: true }
);

panel.webview.html = `
    <html>
        <body>
            <h1>Login</h1>
            <input type="text" id="username" />
            <input type="password" id="password" />
            <button onclick="login()">Login</button>
        </body>
    </html>
`;
```

### 5. **OAuth Flow** (For Third-Party Auth)
```typescript
// Open browser for OAuth
const authUrl = 'https://api.example.com/oauth/authorize';
vscode.env.openExternal(vscode.Uri.parse(authUrl));

// Listen for callback
vscode.env.onDidChangeUri((e) => {
    // Handle OAuth callback
});
```

## 🔐 Secure Token Storage

VS Code provides secure storage for sensitive data:

```typescript
// Store token securely
await context.secrets.store('authToken', token);

// Retrieve token
const token = await context.secrets.get('authToken');

// Delete token (logout)
await context.secrets.delete('authToken');
```

## 📋 Recommended Implementation for Your Extension

### Option 1: Simple Input Prompts (Recommended)
```typescript
// src/auth.ts
import * as vscode from 'vscode';
import axios from 'axios';

const API_BASE = 'http://localhost:5050';

export async function login(context: vscode.ExtensionContext) {
    try {
        // Get credentials
        const username = await vscode.window.showInputBox({
            prompt: 'Username or Email',
            placeHolder: 'Enter your username or email'
        });
        
        if (!username) return;
        
        const password = await vscode.window.showInputBox({
            prompt: 'Password',
            password: true,
            placeHolder: 'Enter your password'
        });
        
        if (!password) return;
        
        // Show progress
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Logging in...",
            cancellable: false
        }, async () => {
            // Call API
            const response = await axios.post(`${API_BASE}/auth/login`, {
                username_or_email: username,
                password: password
            });
            
            if (response.data.ok) {
                // Store token
                await context.secrets.store('authToken', response.data.token);
                await context.secrets.store('username', response.data.user.username);
                
                vscode.window.showInformationMessage(
                    `Logged in as ${response.data.user.username}`
                );
            } else {
                vscode.window.showErrorMessage(response.data.error);
            }
        });
    } catch (error: any) {
        vscode.window.showErrorMessage(`Login failed: ${error.message}`);
    }
}

export async function logout(context: vscode.ExtensionContext) {
    await context.secrets.delete('authToken');
    await context.secrets.delete('username');
    vscode.window.showInformationMessage('Logged out');
}

export async function getAuthToken(context: vscode.ExtensionContext): Promise<string | undefined> {
    return await context.secrets.get('authToken');
}

export async function isAuthenticated(context: vscode.ExtensionContext): Promise<boolean> {
    const token = await getAuthToken(context);
    return !!token;
}
```

### Option 2: Status Bar Integration
```typescript
// src/statusBar.ts
import * as vscode from 'vscode';
import { getAuthToken, isAuthenticated } from './auth';

export function createAuthStatusBar(context: vscode.ExtensionContext) {
    const statusBar = vscode.window.createStatusBarItem(
        vscode.StatusBarAlignment.Right, 100
    );
    
    updateStatusBar(statusBar, context);
    
    // Update when commands are executed
    context.subscriptions.push(
        vscode.commands.registerCommand('smartcursor.refreshAuth', () => {
            updateStatusBar(statusBar, context);
        })
    );
    
    statusBar.show();
    return statusBar;
}

async function updateStatusBar(
    statusBar: vscode.StatusBarItem,
    context: vscode.ExtensionContext
) {
    const authenticated = await isAuthenticated(context);
    
    if (authenticated) {
        const username = await context.secrets.get('username') || 'User';
        statusBar.text = `$(account) ${username}`;
        statusBar.command = 'smartcursor.logout';
        statusBar.tooltip = 'Click to logout';
    } else {
        statusBar.text = '$(sign-in) Login';
        statusBar.command = 'smartcursor.login';
        statusBar.tooltip = 'Click to login';
    }
}
```

### Option 3: Command Registration
```typescript
// src/extension.ts
import * as vscode from 'vscode';
import { login, logout, getAuthToken } from './auth';
import { createAuthStatusBar } from './statusBar';

export function activate(context: vscode.ExtensionContext) {
    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('smartcursor.login', () => login(context)),
        vscode.commands.registerCommand('smartcursor.logout', () => logout(context))
    );
    
    // Create status bar
    createAuthStatusBar(context);
    
    // Check authentication on startup
    checkAuthOnStartup(context);
}

async function checkAuthOnStartup(context: vscode.ExtensionContext) {
    const token = await getAuthToken(context);
    if (!token) {
        const action = await vscode.window.showInformationMessage(
            'Please login to use SmartCursor',
            'Login'
        );
        if (action === 'Login') {
            vscode.commands.executeCommand('smartcursor.login');
        }
    }
}
```

## 🎨 UI Comparison

### Web App (What we built)
```
┌─────────────────────────┐
│   Login Page            │
│                         │
│   Username: [_______]   │
│   Password: [_______]   │
│                         │
│   [Login Button]        │
│   [Register Link]       │
└─────────────────────────┘
```

### VS Code Extension (Recommended)
```
Status Bar: [👤 Login] → Click → Input boxes appear
```

Or:
```
Command Palette (Ctrl+Shift+P):
> SmartCursor: Login
  → Input box: "Username?"
  → Input box: "Password?" (hidden)
  → ✅ Logged in!
```

## ✅ Best Practices

1. **Use Input Boxes** for simple login
2. **Use Status Bar** to show login state
3. **Use Secure Storage** for tokens (context.secrets)
4. **Check Auth** before API calls
5. **Show Progress** during login
6. **Handle Errors** gracefully

## 🚫 What NOT to Do

- ❌ Don't create a full HTML login page (unless OAuth)
- ❌ Don't store tokens in settings (use secrets)
- ❌ Don't show password in plain text
- ❌ Don't require login for every action (cache token)

## 📝 Summary

**For VS Code Extension:**
- ✅ Use `vscode.window.showInputBox()` for credentials
- ✅ Use `context.secrets` for secure token storage
- ✅ Use Status Bar to show login state
- ✅ Use Command Palette commands
- ❌ Don't need full HTML login page

**For Web Application:**
- ✅ Full HTML/CSS login page
- ✅ Form validation
- ✅ Redirect after login
- ✅ Session management

The backend API we built works for BOTH! The extension just uses a simpler UI pattern.

