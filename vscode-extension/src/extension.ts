import * as vscode from 'vscode';
import axios from 'axios';
import * as path from 'path';
import * as fs from 'fs';
import * as os from 'os';
import * as http from 'http';
import * as https from 'https';
import { login, signup, logout, showProfile, isAuthenticated, getAuthHeaders } from './auth';
import { createAuthStatusBar, updateAuthStatusBar } from './statusBar';
import { selectLanguage } from './i18n';

const SERVER_URL = 'http://127.0.0.1:5050';

/**
 * Helper function to handle Server-Sent Events (SSE) streaming from backend.
 * Parses SSE chunks and calls callbacks for different event types.
 */
async function streamSSE(
    url: string,
    body: any,
    callbacks: {
        onStart?: () => void;
        onChunk?: (content: string) => void;
        onDone?: (metadata: any) => void;
        onError?: (error: string) => void;
    },
    token?: vscode.CancellationToken
): Promise<void> {
    return new Promise((resolve, reject) => {
        const urlObj = new URL(url);
        const isHttps = urlObj.protocol === 'https:';
        const httpModule = isHttps ? https : http;
        
        const postData = JSON.stringify(body);
        const options = {
            hostname: urlObj.hostname,
            port: urlObj.port || (isHttps ? 443 : 80),
            path: urlObj.pathname,
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(postData),
                'Accept': 'text/event-stream',
                'Cache-Control': 'no-cache'
            }
        };

        const req = httpModule.request(options, (res) => {
            let buffer = '';
            
            res.on('data', (chunk: Buffer) => {
                if (token?.isCancellationRequested) {
                    req.destroy();
                    return;
                }
                
                buffer += chunk.toString('utf-8');
                const lines = buffer.split('\n');
                buffer = lines.pop() || ''; // Keep incomplete line in buffer
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const dataStr = line.slice(6); // Remove 'data: ' prefix
                        try {
                            const data = JSON.parse(dataStr);
                            
                            if (data.type === 'start' && callbacks.onStart) {
                                callbacks.onStart();
                            } else if (data.type === 'chunk' && callbacks.onChunk) {
                                callbacks.onChunk(data.content || '');
                            } else if (data.type === 'done' && callbacks.onDone) {
                                callbacks.onDone(data);
                                resolve();
                                return;
                            } else if (data.type === 'error' && callbacks.onError) {
                                callbacks.onError(data.error || 'Unknown error');
                                reject(new Error(data.error || 'Unknown error'));
                                return;
                            }
                        } catch (e) {
                            // Skip invalid JSON
                            console.warn('[streamSSE] Failed to parse JSON:', dataStr.substring(0, 100));
                        }
                    }
                }
            });
            
            res.on('end', () => {
                if (buffer) {
                    // Process remaining buffer
                    if (buffer.startsWith('data: ')) {
                        const dataStr = buffer.slice(6);
                        try {
                            const data = JSON.parse(dataStr);
                            if (data.type === 'done' && callbacks.onDone) {
                                callbacks.onDone(data);
                            }
                        } catch (e) {
                            // Ignore parse errors
                        }
                    }
                }
                resolve();
            });
            
            res.on('error', (err: Error) => {
                reject(err);
            });
        });
        
        req.on('error', (err: Error) => {
            reject(err);
        });
        
        // Handle cancellation
        if (token) {
            token.onCancellationRequested(() => {
                req.destroy();
            });
        }
        
        req.write(postData);
        req.end();
    });
}

export function activate(context: vscode.ExtensionContext) {
    console.log('Code Assistant extension is now active!');
    
    // Show activation message
    setTimeout(() => {
        vscode.window.showInformationMessage('Code Assistant extension activated! Type "Code Assistant" in Command Palette.');
    }, 1000);

    // Register commands
    const indexRepoCmd = vscode.commands.registerCommand('codeAssistant.indexRepo', async () => {
        await indexRepository(context);
    });

    const chatCmd = vscode.commands.registerCommand('codeAssistant.chat', async () => {
        await openChatPanel();
    });

    const openChatCmd = vscode.commands.registerCommand('codeAssistant.openChat', async () => {
        await openChatPanel();
    });

    const editSelectionCmd = vscode.commands.registerCommand('codeAssistant.editSelection', async () => {
        console.log('[codeAssistant] editSelection command triggered');
        await editSelectionWithAI();
    });

    const generateTestsCmd = vscode.commands.registerCommand('codeAssistant.generateTests', async () => {
        await generateTestsForSelection();
    });

    const generateDocsCmd = vscode.commands.registerCommand('codeAssistant.generateDocs', async () => {
        await generateDocsForSelection();
    });

    const refactorCmd = vscode.commands.registerCommand('codeAssistant.refactor', async () => {
        await refactorSelection();
    });

    const explainCmd = vscode.commands.registerCommand('codeAssistant.explain', async () => {
        await explainCode();
    });

    const reviewCmd = vscode.commands.registerCommand('codeAssistant.review', async () => {
        await reviewSelection();
    });

    // Register authentication commands
    const loginCmd = vscode.commands.registerCommand('codeAssistant.login', async () => {
        await login(context);
    });

    const signupCmd = vscode.commands.registerCommand('codeAssistant.signup', async () => {
        await signup(context);
    });

    const logoutCmd = vscode.commands.registerCommand('codeAssistant.logout', async () => {
        await logout(context);
    });

    const profileCmd = vscode.commands.registerCommand('codeAssistant.profile', async () => {
        await showProfile(context);
    });

    const selectLanguageCmd = vscode.commands.registerCommand('codeAssistant.selectLanguage', async () => {
        await selectLanguage(context);
    });

    const generateProjectCmd = vscode.commands.registerCommand('codeAssistant.generateProject', async () => {
        await generateProject(context);
    });

    // Register inline completion provider (like Cursor's Tab feature)
    // This provides inline suggestions that appear as grayed-out ghost text
    // Users can press Tab to accept the suggestion
    const inlineCompletionProvider = vscode.languages.registerInlineCompletionItemProvider(
        { scheme: 'file' }, // Support all file types
        {
            async provideInlineCompletionItems(
                document: vscode.TextDocument,
                position: vscode.Position,
                context: vscode.InlineCompletionContext,
                token: vscode.CancellationToken
            ): Promise<vscode.InlineCompletionItem[] | undefined> {
                try {
                    // Get configuration to check if completion is enabled
                    const config = vscode.workspace.getConfiguration('codeAssistant');
                    const completionEnabled = config.get<boolean>('enableInlineCompletion', true);
                    
                    if (!completionEnabled) {
                        return undefined;
                    }

                    // Get workspace folder for repo_dir
                    const workspaceFolders = vscode.workspace.workspaceFolders;
                    if (!workspaceFolders || workspaceFolders.length === 0) {
                        return undefined;
                    }

                    const repoPath = workspaceFolders[0].uri.fsPath;
                    const filePath = document.uri.fsPath;
                    const fileContent = document.getText();
                    const cursorLine = position.line + 1; // VS Code uses 0-indexed, API uses 1-indexed
                    const cursorColumn = position.character + 1; // VS Code uses 0-indexed, API uses 1-indexed

                    // Get current line context
                    const currentLine = document.lineAt(position.line);
                    const textBeforeCursor = currentLine.text.substring(0, position.character);
                    const textAfterCursor = currentLine.text.substring(position.character);
                    
                    // Skip if cursor is in the middle of a word (to avoid interrupting typing)
                    // Only suggest when at end of line or after whitespace
                    if (textBeforeCursor && !textBeforeCursor.match(/[\s\n;{}()\[\],]$/) && textAfterCursor.match(/^\w/)) {
                        return undefined;
                    }

                    console.log(`[completion] Requesting inline completion for ${path.basename(filePath)}:${cursorLine}:${cursorColumn}`);

                    // Call completion endpoint
                    const response = await axios.post(`${SERVER_URL}/completion`, {
                        file_path: filePath,
                        file_content: fileContent,
                        cursor_line: cursorLine,
                        cursor_column: cursorColumn,
                        repo_dir: repoPath,
                        num_completions: 1,
                        max_tokens: 200
                    }, {
                        timeout: 10000 // 10 second timeout for completions
                    });

                    // Check for cancellation
                    if (token.isCancellationRequested) {
                        return undefined;
                    }

                    if (response.data.ok && response.data.primary_completion) {
                        const completion = response.data.primary_completion.trim();
                        
                        if (!completion) {
                            return undefined;
                        }

                        // Create inline completion item (will appear as ghost text)
                        const inlineCompletion = new vscode.InlineCompletionItem(completion);
                        
                        console.log(`[completion] Generated inline completion (${completion.length} chars): ${completion.substring(0, 60).replace(/\n/g, ' ')}...`);
                        
                        return [inlineCompletion];
                    } else {
                        console.log('[completion] No completion generated');
                        return undefined;
                    }
                } catch (error: any) {
                    // Check if it's a cancellation error - don't log those
                    if (axios.isCancel && axios.isCancel(error)) {
                        return undefined;
                    }
                    if (error.code === 'ECONNABORTED' || error.message?.includes('cancel')) {
                        return undefined;
                    }
                    console.error('[completion] Error:', error.message);
                    // Don't show error to user - just silently fail
                    return undefined;
                }
            }
        }
    );

    // Register hover provider for AI explanations
    const hoverProvider = vscode.languages.registerHoverProvider(
        { scheme: 'file' },
        {
            provideHover: async (document, position, token) => {
                const config = vscode.workspace.getConfiguration('codeAssistant');
                const hoverEnabled = config.get<boolean>('enableHoverTooltips', true);
                
                if (!hoverEnabled) {
                    return undefined;
                }
                
                return await provideHoverTooltip(document, position, token);
            }
        }
    );

    // Create status bar item for chat (lower priority than auth status bar)
    const statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 150);
    statusBarItem.command = 'codeAssistant.openChat';
    statusBarItem.text = '$(comment-discussion) AI';
    statusBarItem.tooltip = 'Code Assistant - Click to open chat';
    statusBarItem.show();

    // Create authentication status bar
    const authStatusBar = createAuthStatusBar(context);

    context.subscriptions.push(
        indexRepoCmd, 
        chatCmd, 
        openChatCmd, 
        editSelectionCmd,
        generateTestsCmd,
        generateDocsCmd,
        refactorCmd,
        explainCmd,
        reviewCmd,
        loginCmd,
        signupCmd,
        logoutCmd,
        profileCmd,
        selectLanguageCmd,
        inlineCompletionProvider,
        hoverProvider,
        statusBarItem,
        authStatusBar
    );

    // Check authentication on startup (optional - don't force login)
    setTimeout(async () => {
        const authenticated = await isAuthenticated(context);
        if (!authenticated) {
            // Optionally show a subtle notification
            // vscode.window.showInformationMessage(
            //     'Code Assistant: Login to sync your data across devices',
            //     'Login',
            //     'Sign Up'
            // ).then(selection => {
            //     if (selection === 'Login') {
            //         vscode.commands.executeCommand('codeAssistant.login');
            //     } else if (selection === 'Sign Up') {
            //         vscode.commands.executeCommand('codeAssistant.signup');
            //     }
            // });
        }
    }, 2000);
    
    console.log('Code Assistant commands registered:', [
        'codeAssistant.indexRepo',
        'codeAssistant.chat',
        'codeAssistant.openChat',
        'codeAssistant.editSelection',
        'Code Completion Provider'
    ]);
}

async function indexRepository(context: vscode.ExtensionContext) {
    // Check authentication first
    const authenticated = await isAuthenticated(context);
    if (!authenticated) {
        const action = await vscode.window.showWarningMessage(
            'You need to login first to index repositories. Would you like to login now?',
            'Login',
            'Sign Up',
            'Cancel'
        );
        
        if (action === 'Login') {
            await login(context);
            // Retry indexing after login
            const retry = await vscode.window.showInformationMessage(
                'Login successful! Would you like to index the repository now?',
                'Yes',
                'No'
            );
            if (retry === 'Yes') {
                await indexRepository(context);
            }
            return;
        } else if (action === 'Sign Up') {
            await signup(context);
            // Retry indexing after signup
            const retry = await vscode.window.showInformationMessage(
                'Account created! Would you like to index the repository now?',
                'Yes',
                'No'
            );
            if (retry === 'Yes') {
                await indexRepository(context);
            }
            return;
        }
        return;
    }

    const workspaceFolders = vscode.workspace.workspaceFolders;
    
    if (!workspaceFolders || workspaceFolders.length === 0) {
        vscode.window.showErrorMessage('No workspace folder open. Please open a folder first.');
        return;
    }

    const repoPath = workspaceFolders[0].uri.fsPath;
    
    const confirm = await vscode.window.showInformationMessage(
        `Index repository: ${path.basename(repoPath)}?`,
        'Yes', 'No'
    );

    if (confirm !== 'Yes') {
        return;
    }

    const statusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBar.text = "$(sync~spin) Indexing repository...";
    statusBar.show();

    try {
        // Get auth headers
        const headers = await getAuthHeaders(context);
        
        const response = await axios.post(`${SERVER_URL}/index_repo`, {
            repo_dir: repoPath
        }, {
            headers: headers,
            timeout: 300000 // 5 minutes timeout
        });

        if (response.data.ok) {
            statusBar.hide();
            vscode.window.showInformationMessage(
                `✅ Repository indexed successfully! Found ${response.data.chunks} chunks.`,
                'Open Chat'
            ).then(selection => {
                if (selection === 'Open Chat') {
                    openChatPanel();
                }
            });
        } else {
            statusBar.hide();
            vscode.window.showErrorMessage(`Error: ${response.data.error}`);
        }
    } catch (error: any) {
        statusBar.hide();
        const errorMsg = error.response?.data?.error || error.message || 'Unknown error';
        vscode.window.showErrorMessage(`Failed to index repository: ${errorMsg}`);
    }
}

async function generateProject(context: vscode.ExtensionContext): Promise<void> {
    try {
        // Check authentication
        if (!(await isAuthenticated(context))) {
            const action = await vscode.window.showInformationMessage(
                'Please login or sign up to generate projects.',
                'Login',
                'Sign Up'
            );
            if (action === 'Login') {
                await login(context);
            } else if (action === 'Sign Up') {
                await signup(context);
            }
            // Retry after login/signup
            if (await isAuthenticated(context)) {
                await generateProject(context);
            }
            return;
        }

        // Get project description from user
        const description = await vscode.window.showInputBox({
            prompt: 'Describe the project you want to generate (e.g., "A todo app with React frontend and Flask backend")',
            placeHolder: 'Enter project description...',
            validateInput: (value) => {
                if (!value || value.trim().length === 0) {
                    return 'Please enter a project description';
                }
                if (value.trim().length < 10) {
                    return 'Please provide more details (at least 10 characters)';
                }
                return null;
            }
        });

        if (!description) {
            return; // User cancelled
        }

        // Ask for preferred programming languages (optional)
        const preferredLanguages = await vscode.window.showQuickPick([
            {
                label: 'Auto-detect from existing code',
                value: null,
                description: 'Detect languages from code in the target folder (if exists)'
            },
            {
                label: 'Python (Backend) + JavaScript (Frontend)',
                value: { backend: 'python', frontend: 'javascript' },
                description: 'Python for backend, JavaScript for frontend'
            },
            {
                label: 'TypeScript (Frontend) + Node.js (Backend)',
                value: { backend: 'nodejs', frontend: 'typescript' },
                description: 'TypeScript for frontend, Node.js for backend'
            },
            {
                label: 'Python (Backend) + TypeScript (Frontend)',
                value: { backend: 'python', frontend: 'typescript' },
                description: 'Python for backend, TypeScript for frontend'
            },
            {
                label: 'Java (Backend) + TypeScript (Frontend)',
                value: { backend: 'java', frontend: 'typescript' },
                description: 'Java for backend, TypeScript for frontend'
            },
            {
                label: 'Go (Backend) + JavaScript (Frontend)',
                value: { backend: 'go', frontend: 'javascript' },
                description: 'Go for backend, JavaScript for frontend'
            },
            {
                label: 'Rust (Backend) + TypeScript (Frontend)',
                value: { backend: 'rust', frontend: 'typescript' },
                description: 'Rust for backend, TypeScript for frontend'
            },
            {
                label: 'Custom (specify in description)',
                value: null,
                description: 'Specify languages in your project description'
            }
        ], {
            placeHolder: 'Select preferred programming languages (or Auto-detect)',
            ignoreFocusOut: true
        });

        let preferredLanguage = null;
        if (preferredLanguages && preferredLanguages.value) {
            preferredLanguage = preferredLanguages.value;
        }

        // Get workspace folder (optional - can generate in current folder or new folder)
        const workspaceFolders = vscode.workspace.workspaceFolders;
        let targetPath: string;
        
        // Check if target path exists and has code
        let hasExistingCode = false;
        let detectedStack: any = null;
        
        if (workspaceFolders && workspaceFolders.length > 0) {
            // Use current workspace
            targetPath = workspaceFolders[0].uri.fsPath;
            // Check if directory has code files
            const fs = require('fs');
            const path = require('path');
            try {
                const files = fs.readdirSync(targetPath, { withFileTypes: true });
                const hasCodeFiles = files.some((file: any) => {
                    if (file.isFile()) {
                        const ext = path.extname(file.name).toLowerCase();
                        return ['.py', '.js', '.ts', '.java', '.go', '.rs', '.cpp', '.c', '.php', '.rb'].includes(ext);
                    }
                    return false;
                });
                
                if (!hasCodeFiles) {
                    // No existing code - ask user to choose stack
                    const frontendOptions = ['React', 'Vue.js', 'Angular', 'Next.js', 'HTML/CSS/JS'];
                    const backendOptions = ['Flask (Python)', 'Django (Python)', 'FastAPI (Python)', 'Express.js (Node.js)', 'Spring Boot (Java)'];
                    const databaseOptions = ['SQLite', 'PostgreSQL', 'MySQL', 'MongoDB'];
                    
                    const frontend = await vscode.window.showQuickPick(
                        frontendOptions.map(opt => ({ label: opt, value: opt.toLowerCase().replace(' ', '-').replace('(', '').replace(')', '') })),
                        { placeHolder: 'Select frontend framework (or skip to auto-detect)' }
                    );
                    
                    const backend = await vscode.window.showQuickPick(
                        backendOptions.map(opt => ({ label: opt, value: opt.toLowerCase().split(' ')[0] })),
                        { placeHolder: 'Select backend framework (or skip to auto-detect)' }
                    );
                    
                    const database = await vscode.window.showQuickPick(
                        databaseOptions.map(opt => ({ label: opt, value: opt.toLowerCase() })),
                        { placeHolder: 'Select database (or skip to auto-detect)' }
                    );
                    
                    if (frontend || backend || database) {
                        detectedStack = {
                            frontend: frontend?.value || undefined,
                            backend: backend?.value || undefined,
                            database: database?.value || undefined
                        };
                    }
                }
            } catch (error) {
                // Ignore errors, will use auto-detection
            }
        } else {
            // Ask user to select/create a folder
            const folderUri = await vscode.window.showOpenDialog({
                canSelectFiles: false,
                canSelectFolders: true,
                canSelectMany: false,
                openLabel: 'Select Folder for Project'
            });
            
            if (!folderUri || folderUri.length === 0) {
                vscode.window.showInformationMessage('Project generation cancelled.');
                return;
            }
            
            targetPath = folderUri[0].fsPath;
        }

        // Check if target path has existing code
        try {
            const fs = require('fs');
            if (fs.existsSync(targetPath)) {
                const files = fs.readdirSync(targetPath);
                const codeFiles = files.filter((f: string) => 
                    /\.(py|js|ts|jsx|tsx|java|go|rs|cpp|c|php|rb|swift|kt)$/i.test(f)
                );
                hasExistingCode = codeFiles.length > 0;
            }
        } catch (e) {
            // Ignore errors checking for existing code
        }

        // Show progress
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: 'Generating Project',
            cancellable: true
        }, async (progress, token) => {
            progress.report({ increment: 0, message: 'Sending request to server...' });

            try {
                const authHeaders = await getAuthHeaders(context);
                const requestBody: any = {
                    description: description.trim(),
                    repo_path: targetPath,
                    dry_run: false,
                    apply: true
                };
                
                // Add stack preferences if user selected them
                if (detectedStack) {
                    requestBody.stack = detectedStack;
                }
                
                // Add preferred_languages if selected (full stack selection)
                if (preferredLanguage) {
                    requestBody.preferred_languages = preferredLanguage;
                }
                
                const response = await axios.post(
                    `${SERVER_URL}/generate_project`,
                    requestBody,
                    {
                        headers: authHeaders,
                        timeout: 300000, // 5 minutes for project generation
                    }
                );

                if (response.data.ok) {
                    progress.report({ increment: 50, message: 'Project generated successfully!' });
                    
                    const projectPath = response.data.project_path || targetPath;
                    const message = `✅ Project generated successfully!\n\nLocation: ${projectPath}\n\nWould you like to open the project folder?`;
                    
                    const action = await vscode.window.showInformationMessage(
                        message,
                        'Open Folder',
                        'Open in New Window'
                    );
                    
                    if (action === 'Open Folder') {
                        // Open in current window
                        await vscode.commands.executeCommand('vscode.openFolder', vscode.Uri.file(projectPath));
                    } else if (action === 'Open in New Window') {
                        // Open in new window
                        await vscode.commands.executeCommand('vscode.openFolder', vscode.Uri.file(projectPath), true);
                    }
                } else {
                    throw new Error(response.data.error || 'Failed to generate project');
                }
            } catch (error: any) {
                const errorMsg = error.response?.data?.error || error.message || 'Unknown error';
                vscode.window.showErrorMessage(`❌ Failed to generate project: ${errorMsg}`);
                throw error;
            }
        });
    } catch (error: any) {
        const errorMsg = error.message || 'Unknown error';
        vscode.window.showErrorMessage(`❌ Failed to generate project: ${errorMsg}`);
    }
}

async function openChat() {
    await openChatPanel();
}

async function openChatPanel() {
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (!workspaceFolders || workspaceFolders.length === 0) {
        vscode.window.showErrorMessage('Please open a workspace folder first.');
        return;
    }

    const repoPath = workspaceFolders[0].uri.fsPath;

    // Create and show webview
    const panel = vscode.window.createWebviewPanel(
        'codeAssistantChat',
        'Code Assistant Chat',
        vscode.ViewColumn.Beside,
        {
            enableScripts: true,
            retainContextWhenHidden: true
        }
    );

    panel.webview.html = getWebviewContent(repoPath);
    
    // Handle messages from webview
    panel.webview.onDidReceiveMessage(async message => {
        switch (message.command) {
            case 'askQuestion':
                await handleQuestion(
                    panel, 
                    message.repoPath, 
                    message.question, 
                    message.analysisType || null,
                    message.autoDetect !== false  // Default to true if not specified
                );
                break;
        }
    }, undefined);
}

function getWebviewContent(repoPath: string): string {
    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Code Assistant Chat</title>
    <style>
        body {
            font-family: var(--vscode-font-family);
            padding: 20px;
            color: var(--vscode-foreground);
            background: var(--vscode-editor-background);
        }
        .chat-container {
            display: flex;
            flex-direction: column;
            height: 100vh;
        }
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            margin-bottom: 20px;
            padding: 10px;
        }
        .message {
            margin-bottom: 20px;
            padding: 15px;
            border-radius: 8px;
            background: var(--vscode-input-background);
        }
        .message.user {
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
        }
        .message.assistant {
            background: var(--vscode-input-background);
        }
        .input-area {
            display: flex;
            flex-direction: column;
            gap: 10px;
            border-top: 1px solid var(--vscode-input-border);
            padding-top: 20px;
        }
        textarea {
            width: 100%;
            min-height: 100px;
            padding: 10px;
            background: var(--vscode-input-background);
            color: var(--vscode-input-foreground);
            border: 1px solid var(--vscode-input-border);
            border-radius: 4px;
            font-family: inherit;
        }
        select {
            padding: 8px;
            background: var(--vscode-input-background);
            color: var(--vscode-input-foreground);
            border: 1px solid var(--vscode-input-border);
            border-radius: 4px;
        }
        button {
            padding: 10px 20px;
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            opacity: 0.8;
        }
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .repo-info {
            padding: 10px;
            background: var(--vscode-input-background);
            border-radius: 4px;
            margin-bottom: 15px;
            font-size: 0.9em;
        }
        code {
            background: var(--vscode-textCodeBlock-background);
            padding: 2px 6px;
            border-radius: 3px;
        }
        pre {
            background: var(--vscode-textCodeBlock-background);
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="repo-info">
            📁 Repository: <code>${repoPath.replace(/\\/g, '/')}</code>
        </div>
        <div class="chat-messages" id="messages">
            <div class="message assistant">
                👋 Welcome! Ask me questions about your codebase.
            </div>
        </div>
        <div class="input-area">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                <label style="font-size: 0.9em; color: var(--vscode-descriptionForeground);">
                    <input type="checkbox" id="autoDetectMode" checked style="margin-right: 5px;">
                    Auto-detect analysis type
                </label>
                <select id="analysisType" style="flex: 1; display: none;">
                    <option value="explain">Explain - Explain what the code does</option>
                    <option value="refactor">Refactor - Suggest refactoring improvements</option>
                    <option value="debug">Debug - Help identify bugs and issues</option>
                    <option value="optimize">Optimize - Suggest performance optimizations</option>
                    <option value="generate">Generate - Create or generate new code/project</option>
                </select>
            </div>
            <textarea id="questionInput" placeholder="Ask a question about your code... (Ctrl+Enter to send)"></textarea>
            <button id="sendBtn">Send Question</button>
        </div>
    </div>

    <script>
        const vscode = acquireVsCodeApi();
        const questionInput = document.getElementById('questionInput');
        const sendBtn = document.getElementById('sendBtn');
        const messagesDiv = document.getElementById('messages');
        const analysisType = document.getElementById('analysisType');
        const autoDetectCheckbox = document.getElementById('autoDetectMode');
        const repoPath = ${JSON.stringify(repoPath)};
        
        // Toggle manual selection based on auto-detect checkbox
        autoDetectCheckbox.addEventListener('change', (e) => {
            const isAuto = e.target.checked;
            analysisType.style.display = isAuto ? 'none' : 'block';
        });

        function addMessage(content, isUser = false) {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ' + (isUser ? 'user' : 'assistant');
            messageDiv.textContent = content;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        sendBtn.addEventListener('click', () => {
            const question = questionInput.value.trim();
            if (!question) return;

            addMessage(question, true);
            questionInput.value = '';
            sendBtn.disabled = true;
            sendBtn.textContent = 'Loading...';

            // Determine analysis type: auto-detect if checkbox is checked, otherwise use manual selection
            const useAutoDetect = autoDetectCheckbox ? autoDetectCheckbox.checked : true;
            const selectedAnalysisType = useAutoDetect ? null : (analysisType ? analysisType.value : null);
            
            vscode.postMessage({
                command: 'askQuestion',
                repoPath: repoPath,
                question: question,
                analysisType: selectedAnalysisType,
                autoDetect: useAutoDetect
            });
        });

        questionInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
                sendBtn.click();
            }
        });

        // Listen for messages from extension
        window.addEventListener('message', event => {
            const message = event.data;
            if (message.command === 'answer') {
                addMessage(message.answer);
                sendBtn.disabled = false;
                sendBtn.textContent = 'Send Question';
            } else if (message.command === 'error') {
                addMessage('❌ Error: ' + message.error);
                sendBtn.disabled = false;
                sendBtn.textContent = 'Send Question';
            }
        });
    </script>
</body>
</html>`;
}

async function handleQuestion(panel: vscode.WebviewPanel, repoPath: string, question: string, analysisType: string | null, autoDetect: boolean = false) {
    try {
        // If auto-detect is enabled, don't send analysis_type (backend will auto-detect)
        const requestBody: any = {
            repo_dir: repoPath,
            question: question
        };
        
        // Only include analysis_type if manually selected
        if (!autoDetect && analysisType) {
            requestBody.analysis_type = analysisType;
        }
        // If autoDetect is true, backend will automatically detect the analysis type
        
        const response = await axios.post(`${SERVER_URL}/chat`, requestBody, {
            timeout: 90000
        });

        if (response.data.ok) {
            let answerText = response.data.answer;
            
            // Add citations to answer
            if (response.data.citations && response.data.citations.length > 0) {
                answerText += '\n\n📎 Citations:\n';
                response.data.citations.forEach((cit: any) => {
                    const fileName = path.basename(cit.file);
                    answerText += `  - ${fileName}:${cit.start}-${cit.end}\n`;
                });
            }

            panel.webview.postMessage({
                command: 'answer',
                answer: answerText
            });
        } else {
            panel.webview.postMessage({
                command: 'error',
                error: response.data.error || 'Unknown error'
            });
        }
    } catch (error: any) {
        const errorMsg = error.response?.data?.error || error.message || 'Unknown error';
        panel.webview.postMessage({
            command: 'error',
            error: errorMsg
        });
    }
}

async function editSelectionWithAI(): Promise<void> {
    console.log('[codeAssistant] editSelectionWithAI called');
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        console.log('[codeAssistant] No active editor found');
        vscode.window.showWarningMessage('No active editor found. Please open a file first.');
        return;
    }

    const selection = editor.selection;
    console.log('[codeAssistant] Selection:', { isEmpty: selection.isEmpty, start: selection.start, end: selection.end });
    if (selection.isEmpty) {
        console.log('[codeAssistant] Selection is empty');
        vscode.window.showWarningMessage('Please select some code to edit with AI. You can use Ctrl+Alt+E, Ctrl+K then E, or right-click → "Edit Selection with AI".');
        return;
    }

    // Get selected code
    const selectedText = editor.document.getText(selection);
    const filePath = editor.document.uri.fsPath;

    // Get file context (before and after selection)
    const startLine = selection.start.line;
    const endLine = selection.end.line;
    const contextBefore = startLine > 0 ? editor.document.getText(
        new vscode.Range(Math.max(0, startLine - 10), 0, startLine, 0)
    ) : '';
    const contextAfter = endLine < editor.document.lineCount - 1 ? editor.document.getText(
        new vscode.Range(endLine + 1, 0, Math.min(editor.document.lineCount, endLine + 11), 0)
    ) : '';
    const fileContext = contextBefore + '\n[SELECTED CODE]\n' + selectedText + '\n[END SELECTED CODE]\n' + contextAfter;

    // Get workspace folder for repo_dir
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (!workspaceFolders || workspaceFolders.length === 0) {
        vscode.window.showWarningMessage('No workspace folder found.');
        return;
    }
    const repoDir = workspaceFolders[0].uri.fsPath;

    // Prompt user for edit instruction
    const instruction = await vscode.window.showInputBox({
        prompt: 'How would you like to edit this code?',
        placeHolder: 'e.g., "Add error handling", "Optimize this function", "Add type hints"',
        validateInput: (value) => {
            if (!value || value.trim().length === 0) {
                return 'Please enter an edit instruction.';
            }
            return null;
        }
    });

    if (!instruction) {
        return; // User cancelled
    }

    // Show progress indicator
    await vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: 'Editing code with AI...',
        cancellable: true
    }, async (progress, token) => {
        try {
            progress.report({ increment: 0, message: 'Analyzing code... (10%)' });
            await new Promise(resolve => setTimeout(resolve, 300));
            
            if (token.isCancellationRequested) {
                return;
            }
            
            progress.report({ increment: 10, message: 'Preparing edit request... (20%)' });
            let lastReportedPercent = 20;
            
            let editedCodeChunks: string[] = [];
            let editMetadata: any = null;
            
            try {
                await streamSSE(
                    `${SERVER_URL}/edit`,
                    {
                        selected_code: selectedText,
                        instruction: instruction,
                        file_path: filePath,
                        repo_dir: repoDir,
                        file_context: fileContext,
                        stream: true
                    },
                    {
                        onStart: () => {
                            console.log('[edit] Stream started');
                            // Only report 30% when streaming actually starts
                            progress.report({ increment: 10, message: 'Streaming edited code... (30%)' });
                            lastReportedPercent = 30;
                        },
                        onChunk: (content: string) => {
                            editedCodeChunks.push(content);
                            const totalChars = editedCodeChunks.join('').length;
                            const estimatedProgress = Math.min(30 + Math.floor(totalChars / 15), 90);
                            if (estimatedProgress > lastReportedPercent) {
                                const increment = estimatedProgress - lastReportedPercent;
                                lastReportedPercent = estimatedProgress;
                                progress.report({ 
                                    increment: increment, 
                                    message: `AI is editing your code... (${estimatedProgress}%) - ${totalChars} chars` 
                                });
                            }
                        },
                        onDone: (metadata: any) => {
                            console.log('[edit] Stream completed, metadata:', metadata);
                            editMetadata = metadata;
                            progress.report({ increment: 5, message: 'Finalizing... (95%)' });
                            lastReportedPercent = 95;
                        },
                        onError: (error: string) => {
                            console.error('[edit] Stream error:', error);
                            throw new Error(error);
                        }
                    },
                    token
                );
                
                if (token.isCancellationRequested) {
                    return;
                }
                
                const editedCode = editedCodeChunks.join('');
                
                if (!editedCode) {
                    throw new Error('No edited code generated. Please try again.');
                }
                
                progress.report({ increment: 5, message: 'Done! (100%)' });
                
                // Generate diff from metadata or manually
                const diff = editMetadata?.diff || `Original code was edited based on: ${instruction}`;

                // Ask user if they want to apply the edit
                await showDiffAndApply(editor, selection, selectedText, editedCode, diff, filePath);
            } catch (error: any) {
                if (token.isCancellationRequested) {
                    return;
                }
                const errorMsg = error.message || 'Unknown error';
                throw new Error(`Failed to edit code: ${errorMsg}`);
            }

        } catch (error: any) {
            if (token.isCancellationRequested) {
                return;
            }
            const errorMsg = error.message || error.response?.data?.error || 'Unknown error';
            console.error('[edit] Error:', error);
            vscode.window.showErrorMessage(`❌ Failed to edit code: ${errorMsg}`);
        }
    });
}

async function showDiffAndApply(
    editor: vscode.TextEditor,
    selection: vscode.Selection,
    originalCode: string,
    editedCode: string,
    diff: string,
    filePath: string
): Promise<void> {
    // Ask user what they want to do
    const action = await vscode.window.showInformationMessage(
        'AI has generated an edit. What would you like to do?',
        'Preview Diff',
        'Apply Directly',
        'Cancel'
    );

    if (action === 'Cancel' || !action) {
        return;
    }

    if (action === 'Preview Diff') {
        // Show diff preview in VS Code's diff editor
        await showDiffPreview(editor, selection, originalCode, editedCode, filePath);
    } else if (action === 'Apply Directly') {
        await applyEdit(editor, selection, editedCode);
    }
}

async function showDiffPreview(
    editor: vscode.TextEditor,
    selection: vscode.Selection,
    originalCode: string,
    editedCode: string,
    filePath: string
): Promise<void> {
    const tempDir = os.tmpdir();
    const fileName = path.basename(filePath);
    const fileExt = path.extname(fileName);
    const baseName = path.basename(fileName, fileExt);
    const timestamp = Date.now();
    
    const originalTempFile = path.join(tempDir, `${baseName}.original.${timestamp}${fileExt}`);
    const editedTempFile = path.join(tempDir, `${baseName}.edited.${timestamp}${fileExt}`);
    
    let originalUri: vscode.Uri | undefined;
    let editedUri: vscode.Uri | undefined;
    
    try {
        // Write original and edited code to temporary files
        fs.writeFileSync(originalTempFile, originalCode, 'utf8');
        fs.writeFileSync(editedTempFile, editedCode, 'utf8');
        
        // Create URIs for the temporary files
        originalUri = vscode.Uri.file(originalTempFile);
        editedUri = vscode.Uri.file(editedTempFile);
        
        // Open the files to ensure they're loaded
        const originalDoc = await vscode.workspace.openTextDocument(originalUri);
        const editedDoc = await vscode.workspace.openTextDocument(editedUri);
        
        // Wait a moment for files to be ready
        await new Promise(resolve => setTimeout(resolve, 200));
        
        // Open diff view using VS Code's built-in diff command
        await vscode.commands.executeCommand(
            'vscode.diff',
            originalUri,
            editedUri,
            `AI Edit Preview: ${fileName} (Original ↔ Edited)`
        );
        
        // Show message asking if user wants to apply
        const action = await vscode.window.showInformationMessage(
            `Review the diff preview above. Original code is on the left, edited code on the right. Would you like to apply this edit to "${fileName}"?`,
            'Apply Edit',
            'Cancel'
        );
        
        if (action === 'Apply Edit') {
            // Close the diff view first to prevent errors in Problems panel
            await vscode.commands.executeCommand('workbench.action.closeActiveEditor');
            
            // Close any open editors for temporary files
            const editors = vscode.window.visibleTextEditors;
            for (const ed of editors) {
                const docUri = ed.document.uri.fsPath;
                if (docUri === originalTempFile || docUri === editedTempFile) {
                    await vscode.window.showTextDocument(ed.document, { preview: false });
                    await vscode.commands.executeCommand('workbench.action.closeActiveEditor');
                }
            }
            
            // Apply the edit
            await applyEdit(editor, selection, editedCode);
            
            // Clean up temporary files after a short delay
            setTimeout(() => {
                try {
                    // Close any documents that might still be open
                    const docsToClose = vscode.workspace.textDocuments.filter(doc => 
                        doc.uri.fsPath === originalTempFile || doc.uri.fsPath === editedTempFile
                    );
                    docsToClose.forEach(async doc => {
                        try {
                            const editor = vscode.window.visibleTextEditors.find(e => e.document === doc);
                            if (editor) {
                                await vscode.window.showTextDocument(doc, { preview: false });
                                await vscode.commands.executeCommand('workbench.action.closeActiveEditor');
                            }
                        } catch (e) {
                            // Ignore errors closing individual docs
                        }
                    });
                    
                    // Delete temporary files
                    if (fs.existsSync(originalTempFile)) {
                        fs.unlinkSync(originalTempFile);
                    }
                    if (fs.existsSync(editedTempFile)) {
                        fs.unlinkSync(editedTempFile);
                    }
                } catch (cleanupError) {
                    // Ignore cleanup errors
                    console.warn('[diff] Could not clean up temp files:', cleanupError);
                }
            }, 500);
        } else {
            // User cancelled - close diff view and clean up
            await vscode.commands.executeCommand('workbench.action.closeActiveEditor');
            
            // Close any open editors for temporary files
            const editors = vscode.window.visibleTextEditors;
            for (const ed of editors) {
                const docUri = ed.document.uri.fsPath;
                if (docUri === originalTempFile || docUri === editedTempFile) {
                    await vscode.window.showTextDocument(ed.document, { preview: false });
                    await vscode.commands.executeCommand('workbench.action.closeActiveEditor');
                }
            }
            
            // Clean up temporary files
            setTimeout(() => {
                try {
                    // Close any documents that might still be open
                    const docsToClose = vscode.workspace.textDocuments.filter(doc => 
                        doc.uri.fsPath === originalTempFile || doc.uri.fsPath === editedTempFile
                    );
                    docsToClose.forEach(async doc => {
                        try {
                            const editor = vscode.window.visibleTextEditors.find(e => e.document === doc);
                            if (editor) {
                                await vscode.window.showTextDocument(doc, { preview: false });
                                await vscode.commands.executeCommand('workbench.action.closeActiveEditor');
                            }
                        } catch (e) {
                            // Ignore errors closing individual docs
                        }
                    });
                    
                    // Delete temporary files
                    if (fs.existsSync(originalTempFile)) {
                        fs.unlinkSync(originalTempFile);
                    }
                    if (fs.existsSync(editedTempFile)) {
                        fs.unlinkSync(editedTempFile);
                    }
                } catch (cleanupError) {
                    // Ignore cleanup errors
                    console.warn('[diff] Could not clean up temp files:', cleanupError);
                }
            }, 500);
        }
        
    } catch (error: any) {
        console.error('[diff] Error showing diff preview:', error);
        vscode.window.showErrorMessage(`Failed to show diff preview: ${error.message}`);
        
        // Clean up temp files on error
        try {
            if (fs.existsSync(originalTempFile)) {
                fs.unlinkSync(originalTempFile);
            }
            if (fs.existsSync(editedTempFile)) {
                fs.unlinkSync(editedTempFile);
            }
        } catch (cleanupError) {
            // Ignore cleanup errors
        }
        
        // Fallback: ask if user wants to apply without preview
        const applyAction = await vscode.window.showWarningMessage(
            'Could not show visual diff preview. Would you like to apply the edit anyway?',
            'Apply Edit',
            'Cancel'
        );
        
        if (applyAction === 'Apply Edit') {
            await applyEdit(editor, selection, editedCode);
        }
    }
}

async function applyEdit(
    editor: vscode.TextEditor,
    selection: vscode.Selection,
    editedCode: string
): Promise<void> {
    // Apply the edit using WorkspaceEdit
    const workspaceEdit = new vscode.WorkspaceEdit();
    workspaceEdit.replace(
        editor.document.uri,
        selection,
        editedCode
    );

    const applied = await vscode.workspace.applyEdit(workspaceEdit);
    if (applied) {
        vscode.window.showInformationMessage('Edit applied successfully!');
    } else {
        vscode.window.showErrorMessage('Failed to apply edit.');
    }
}

// New command functions for enhanced integration
async function generateTestsForSelection(): Promise<void> {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showWarningMessage('No active editor found.');
        return;
    }

    const selection = editor.selection;
    if (selection.isEmpty) {
        vscode.window.showWarningMessage('Please select some code to generate tests for.');
        return;
    }

    const selectedCode = editor.document.getText(selection);
    const filePath = editor.document.uri.fsPath;

    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (!workspaceFolders || workspaceFolders.length === 0) {
        vscode.window.showWarningMessage('No workspace folder found.');
        return;
    }
    const repoDir = workspaceFolders[0].uri.fsPath;

    await vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: 'Generating tests...',
        cancellable: true
    }, async (progress, token) => {
        try {
            // Start at 0% - make it visible for longer
            progress.report({ increment: 0, message: 'Analyzing code... (0%)' });
            let lastReportedPercent = 0;
            await new Promise(resolve => setTimeout(resolve, 500)); // Longer delay to make 0% visible
            
            if (token.isCancellationRequested) {
                return;
            }
            
            // Go to 10% - visible transition
            progress.report({ increment: 10, message: 'Searching codebase context... (10%)' });
            lastReportedPercent = 10;
            await new Promise(resolve => setTimeout(resolve, 400)); // Delay to make 10% visible
            
            if (token.isCancellationRequested) {
                return;
            }
            
            // Progress to 20% while preparing request
            progress.report({ increment: 10, message: 'Preparing request... (20%)' });
            lastReportedPercent = 20;
            await new Promise(resolve => setTimeout(resolve, 300)); // Delay to make 20% visible
            
            if (token.isCancellationRequested) {
                return;
            }
            
            console.log('[generateTests] Starting streaming request to:', `${SERVER_URL}/generate_tests`);
            
            let testCodeChunks: string[] = [];
            let testMetadata: any = null;
            
            try {
                await streamSSE(
                    `${SERVER_URL}/generate_tests`,
                    {
                        code_snippet: selectedCode,
                        repo_dir: repoDir,
                        test_type: "unit",
                        stream: true
                    },
                    {
                        onStart: () => {
                            console.log('[generateTests] Stream started');
                            // Only report 30% when streaming actually starts (from 20%)
                            progress.report({ increment: 10, message: 'Streaming test code... (30%)' });
                            lastReportedPercent = 30;
                        },
                        onChunk: (content: string) => {
                            testCodeChunks.push(content);
                            // Update progress based on chunks received
                            const totalChars = testCodeChunks.join('').length;
                            // Progress from 30% to 90% based on chunks received
                            // Use a more gradual calculation: every 20 chars = 1% progress (from 30% to 90%)
                            const estimatedProgress = Math.min(30 + Math.floor(totalChars / 20), 90);
                            if (estimatedProgress > lastReportedPercent) {
                                const increment = estimatedProgress - lastReportedPercent;
                                lastReportedPercent = estimatedProgress;
                                progress.report({ 
                                    increment: increment, 
                                    message: `Generating tests... (${estimatedProgress}%) - ${totalChars} chars` 
                                });
                            }
                        },
                        onDone: (metadata: any) => {
                            console.log('[generateTests] Stream completed, metadata:', metadata);
                            testMetadata = metadata;
                            // Progress already at 90%, jump to 95%
                            progress.report({ increment: 5, message: 'Finalizing... (95%)' });
                            lastReportedPercent = 95;
                        },
                        onError: (error: string) => {
                            console.error('[generateTests] Stream error:', error);
                            throw new Error(error);
                        }
                    },
                    token
                );
                
                if (token.isCancellationRequested) {
                    console.log('[generateTests] Cancellation requested');
                    return;
                }
                
                const testCode = testCodeChunks.join('');
                
                if (!testCode) {
                    throw new Error('No test code generated. Please try again.');
                }
                
                // Report 100% completion
                progress.report({ increment: 5, message: 'Done! (100%)' });
                
                console.log('[generateTests] Creating document with', testCode.length, 'chars');
                // Show test code in a new document
                const doc = await vscode.workspace.openTextDocument({
                    content: testCode,
                    language: testMetadata?.language || 'python'
                });
                await vscode.window.showTextDocument(doc, vscode.ViewColumn.Beside);
                console.log('[generateTests] Document shown successfully');

                vscode.window.showInformationMessage(`✅ Tests generated! (${testMetadata?.lines || testCode.split('\n').length} lines)`);
            } catch (error: any) {
                if (token.isCancellationRequested) {
                    return;
                }
                console.error('[generateTests] Error:', error);
                const errorMsg = error.message || 'Unknown error';
                throw new Error(`Failed to generate tests: ${errorMsg}`);
            }

            } catch (error: any) {
                if (token.isCancellationRequested) {
                    return;
                }
                const errorMsg = error.message || 'Unknown error';
                console.error('[generateTests] Error:', error);
                vscode.window.showErrorMessage(`❌ Failed to generate tests: ${errorMsg}`);
            }
    });
}

async function generateDocsForSelection(): Promise<void> {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showWarningMessage('No active editor found.');
        return;
    }

    const selection = editor.selection;
    if (selection.isEmpty) {
        vscode.window.showWarningMessage('Please select some code to generate documentation for.');
        return;
    }

    const selectedCode = editor.document.getText(selection);
    const filePath = editor.document.uri.fsPath;
    const language = editor.document.languageId;

    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (!workspaceFolders || workspaceFolders.length === 0) {
        vscode.window.showWarningMessage('No workspace folder found.');
        return;
    }
    const repoDir = workspaceFolders[0].uri.fsPath;

    await vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: 'Generating documentation...',
        cancellable: true
    }, async (progress, token) => {
        try {
            progress.report({ increment: 0, message: 'Analyzing code... (10%)' });
            await new Promise(resolve => setTimeout(resolve, 300));
            
            if (token.isCancellationRequested) {
                return;
            }
            
            progress.report({ increment: 10, message: 'Searching codebase context... (20%)' });
            let lastReportedPercent = 20;
            
            let docChunks: string[] = [];
            let docMetadata: any = null;
            
            try {
                await streamSSE(
                    `${SERVER_URL}/generate_docs`,
                    {
                        doc_type: "docstring",
                        code_snippet: selectedCode,
                        repo_dir: repoDir,
                        doc_format: language === 'python' ? 'google' : 'jsdoc',
                        stream: true
                    },
                    {
                        onStart: () => {
                            console.log('[generateDocs] Stream started');
                            // Only report 30% when streaming actually starts
                            progress.report({ increment: 10, message: 'Streaming documentation... (30%)' });
                            lastReportedPercent = 30;
                        },
                        onChunk: (content: string) => {
                            docChunks.push(content);
                            const totalChars = docChunks.join('').length;
                            const estimatedProgress = Math.min(30 + Math.floor(totalChars / 20), 90);
                            if (estimatedProgress > lastReportedPercent) {
                                const increment = estimatedProgress - lastReportedPercent;
                                lastReportedPercent = estimatedProgress;
                                progress.report({ 
                                    increment: increment, 
                                    message: `Generating documentation... (${estimatedProgress}%) - ${totalChars} chars` 
                                });
                            }
                        },
                        onDone: (metadata: any) => {
                            console.log('[generateDocs] Stream completed, metadata:', metadata);
                            docMetadata = metadata;
                            progress.report({ increment: 5, message: 'Finalizing... (95%)' });
                            lastReportedPercent = 95;
                        },
                        onError: (error: string) => {
                            console.error('[generateDocs] Stream error:', error);
                            throw new Error(error);
                        }
                    },
                    token
                );
                
                if (token.isCancellationRequested) {
                    return;
                }
                
                const documentation = docChunks.join('');
                
                if (!documentation) {
                    throw new Error('No documentation generated. Please try again.');
                }
                
                progress.report({ increment: 5, message: 'Done! (100%)' });
                
                // Show documentation in output channel or new document
                const doc = await vscode.workspace.openTextDocument({
                    content: documentation,
                    language: docMetadata?.language || language
                });
                await vscode.window.showTextDocument(doc, vscode.ViewColumn.Beside);

                vscode.window.showInformationMessage(`✅ Documentation generated! (${docMetadata?.lines || documentation.split('\n').length} lines)`);
            } catch (error: any) {
                if (token.isCancellationRequested) {
                    return;
                }
                const errorMsg = error.message || 'Unknown error';
                throw new Error(`Failed to generate documentation: ${errorMsg}`);
            }
        } catch (error: any) {
            const errorMsg = error.message || 'Unknown error';
            console.error('[generateDocs] Error:', error);
            vscode.window.showErrorMessage(`❌ Failed to generate documentation: ${errorMsg}`);
        }
    });
}

async function refactorSelection(): Promise<void> {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showWarningMessage('No active editor found.');
        return;
    }

    const selection = editor.selection;
    if (selection.isEmpty) {
        vscode.window.showWarningMessage('Please select some code to refactor.');
        return;
    }

    const filePath = editor.document.uri.fsPath;
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (!workspaceFolders || workspaceFolders.length === 0) {
        vscode.window.showWarningMessage('No workspace folder found.');
        return;
    }
    const repoDir = workspaceFolders[0].uri.fsPath;

    await vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: 'Refactoring code...',
        cancellable: true
    }, async (progress, token) => {
        try {
            progress.report({ increment: 0, message: 'Analyzing code... (10%)' });
            await new Promise(resolve => setTimeout(resolve, 300));
            
            if (token.isCancellationRequested) {
                return;
            }
            
            progress.report({ increment: 10, message: 'Searching codebase... (20%)' });
            let lastReportedPercent = 20;
            
            let suggestionChunks: string[] = [];
            let refactorMetadata: any = null;
            
            try {
                await streamSSE(
                    `${SERVER_URL}/refactor`,
                    {
                        file_path: filePath,
                        repo_dir: repoDir,
                        top_k: 2,
                        stream: true
                    },
                    {
                        onStart: () => {
                            console.log('[refactor] Stream started');
                            // Only report 30% when streaming actually starts
                            progress.report({ increment: 10, message: 'Streaming refactoring suggestions... (30%)' });
                            lastReportedPercent = 30;
                        },
                        onChunk: (content: string) => {
                            suggestionChunks.push(content);
                            const totalChars = suggestionChunks.join('').length;
                            const estimatedProgress = Math.min(30 + Math.floor(totalChars / 30), 90);
                            if (estimatedProgress > lastReportedPercent) {
                                const increment = estimatedProgress - lastReportedPercent;
                                lastReportedPercent = estimatedProgress;
                                progress.report({ 
                                    increment: increment, 
                                    message: `Analyzing code with AI... (${estimatedProgress}%) - ${totalChars} chars` 
                                });
                            }
                        },
                        onDone: (metadata: any) => {
                            console.log('[refactor] Stream completed, metadata:', metadata);
                            refactorMetadata = metadata;
                            progress.report({ increment: 5, message: 'Finalizing... (95%)' });
                            lastReportedPercent = 95;
                        },
                        onError: (error: string) => {
                            console.error('[refactor] Stream error:', error);
                            throw new Error(error);
                        }
                    },
                    token
                );
                
                if (token.isCancellationRequested) {
                    return;
                }
                
                const suggestions = suggestionChunks.join('');
                
                if (!suggestions) {
                    throw new Error('No refactoring suggestions generated. Please try again.');
                }
                
                progress.report({ increment: 5, message: 'Done! (100%)' });
                
                // Show refactoring suggestions in a webview
                const panel = vscode.window.createWebviewPanel(
                    'refactorSuggestions',
                    'Refactoring Suggestions',
                    vscode.ViewColumn.Beside,
                    { enableScripts: true }
                );

                // Render markdown suggestions as HTML
                panel.webview.html = getRefactoringSuggestionsHTMLFromMarkdown(suggestions);
                vscode.window.showInformationMessage(`✅ Refactoring suggestions generated! (${suggestions.split('\n').length} lines)`);
            } catch (error: any) {
                if (token.isCancellationRequested) {
                    return;
                }
                const errorMsg = error.message || 'Unknown error';
                throw new Error(`Failed to refactor code: ${errorMsg}`);
            }
        } catch (error: any) {
            if (token.isCancellationRequested) {
                return;
            }
            const errorMsg = error.message || error.response?.data?.error || 'Unknown error';
            console.error('[refactor] Error:', error);
            vscode.window.showErrorMessage(`❌ Failed to refactor: ${errorMsg}`);
        }
    });
}

async function reviewSelection(): Promise<void> {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showWarningMessage('No active editor found.');
        return;
    }

    const selection = editor.selection;
    if (selection.isEmpty) {
        vscode.window.showWarningMessage('Please select some code to review.');
        return;
    }

    const selectedCode = editor.document.getText(selection);
    const filePath = editor.document.uri.fsPath;
    const language = editor.document.languageId;

    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (!workspaceFolders || workspaceFolders.length === 0) {
        vscode.window.showWarningMessage('No workspace folder found.');
        return;
    }
    const repoDir = workspaceFolders[0].uri.fsPath;

    // Ask user for review type
    const reviewType = await vscode.window.showQuickPick([
        { label: 'Comprehensive Review', value: 'comprehensive', description: 'Review all aspects (bugs, security, performance, quality)' },
        { label: 'Security Review', value: 'security', description: 'Focus on security vulnerabilities' },
        { label: 'Performance Review', value: 'performance', description: 'Focus on performance issues' },
        { label: 'Quality Review', value: 'quality', description: 'Focus on code quality and best practices' },
        { label: 'Bug Detection', value: 'bugs', description: 'Focus on bugs and logic errors' }
    ], {
        placeHolder: 'Select review type',
        canPickMany: false
    });

    if (!reviewType) {
        return; // User cancelled
    }

    await vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: 'Reviewing code...',
        cancellable: true
    }, async (progress, token) => {
        try {
            progress.report({ increment: 0, message: 'Analyzing code... (10%)' });
            await new Promise(resolve => setTimeout(resolve, 300));
            
            if (token.isCancellationRequested) {
                return;
            }
            
            progress.report({ increment: 10, message: 'Searching codebase context... (20%)' });
            let lastReportedPercent = 20;
            
            let reviewChunks: string[] = [];
            let reviewMetadata: any = null;
            
            try {
                await streamSSE(
                    `${SERVER_URL}/review`,
                    {
                        code: selectedCode,
                        file_path: filePath,
                        repo_dir: repoDir,
                        language: language,
                        review_type: reviewType.value,
                        stream: true
                    },
                    {
                        onStart: () => {
                            console.log('[review] Stream started');
                            progress.report({ increment: 10, message: 'Streaming review report... (30%)' });
                            lastReportedPercent = 30;
                        },
                        onChunk: (content: string) => {
                            reviewChunks.push(content);
                            const totalChars = reviewChunks.join('').length;
                            const estimatedProgress = Math.min(30 + Math.floor(totalChars / 25), 90);
                            if (estimatedProgress > lastReportedPercent) {
                                const increment = estimatedProgress - lastReportedPercent;
                                lastReportedPercent = estimatedProgress;
                                progress.report({ 
                                    increment: increment, 
                                    message: `Reviewing code... (${estimatedProgress}%) - ${totalChars} chars` 
                                });
                            }
                        },
                        onDone: (metadata: any) => {
                            console.log('[review] Stream completed, metadata:', metadata);
                            reviewMetadata = metadata;
                            progress.report({ increment: 5, message: 'Finalizing... (95%)' });
                            lastReportedPercent = 95;
                        },
                        onError: (error: string) => {
                            console.error('[review] Stream error:', error);
                            throw new Error(error);
                        }
                    },
                    token
                );
                
                if (token.isCancellationRequested) {
                    return;
                }
                
                const reviewReport = reviewChunks.join('');
                
                if (!reviewReport) {
                    throw new Error('No review report generated. Please try again.');
                }
                
                progress.report({ increment: 5, message: 'Done! (100%)' });
                
                // Show review report in a webview
                const panel = vscode.window.createWebviewPanel(
                    'codeReview',
                    `Code Review - ${path.basename(filePath)}`,
                    vscode.ViewColumn.Beside,
                    { enableScripts: true }
                );

                // Render review report as HTML
                panel.webview.html = getCodeReviewHTML(reviewReport, reviewMetadata);
                
                // Show summary in notification
                const summary = reviewMetadata?.summary || {};
                const totalIssues = summary.total_issues || 0;
                const criticalHigh = summary.critical_high || 0;
                const overallQuality = summary.overall_quality || 'Unknown';
                
                vscode.window.showInformationMessage(
                    `✅ Code review complete! Issues: ${totalIssues} (${criticalHigh} critical/high). Quality: ${overallQuality}`
                );
            } catch (error: any) {
                if (token.isCancellationRequested) {
                    return;
                }
                const errorMsg = error.message || 'Unknown error';
                throw new Error(`Failed to review code: ${errorMsg}`);
            }
        } catch (error: any) {
            if (token.isCancellationRequested) {
                return;
            }
            const errorMsg = error.message || 'Unknown error';
            console.error('[review] Error:', error);
            vscode.window.showErrorMessage(`❌ Failed to review code: ${errorMsg}`);
        }
    });
}

async function explainCode(): Promise<void> {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showWarningMessage('No active editor found.');
        return;
    }

    const selection = editor.selection;
    const selectedCode = selection.isEmpty 
        ? editor.document.lineAt(selection.active.line).text 
        : editor.document.getText(selection);
    
    const filePath = editor.document.uri.fsPath;

    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (!workspaceFolders || workspaceFolders.length === 0) {
        vscode.window.showWarningMessage('No workspace folder found.');
        return;
    }
    const repoDir = workspaceFolders[0].uri.fsPath;

    await vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: 'Explaining code...',
        cancellable: true
    }, async (progress, token) => {
        try {
            progress.report({ increment: 0, message: 'Analyzing code... (10%)' });
            await new Promise(resolve => setTimeout(resolve, 300));
            
            if (token.isCancellationRequested) {
                return;
            }
            
            progress.report({ increment: 10, message: 'Searching codebase context... (20%)' });
            
            const startTime = Date.now();
            let response: any;
            
            try {
                response = await axios.post(`${SERVER_URL}/chat`, {
                    question: `Explain this code: ${selectedCode}`,
                    repo_dir: repoDir,
                    analysis_type: "explain"
                }, {
                    timeout: 60000
                });
                
                if (token.isCancellationRequested) {
                    return;
                }
                
                const elapsed = Date.now() - startTime;
                const progressPercent = Math.min(70 + Math.floor((elapsed / 1000) * 10), 95);
                progress.report({ increment: progressPercent - 30, message: `Generating explanation with AI... (${progressPercent}%)` });
            } catch (axiosError: any) {
                if (token.isCancellationRequested) {
                    return;
                }
                
                if (axiosError.code === 'ECONNABORTED' || axiosError.message?.includes('timeout')) {
                    throw new Error('Request timed out after 1 minute. Please try again.');
                }
                if (axiosError.response) {
                    const errorMsg = axiosError.response.data?.error || 'Unknown server error';
                    throw new Error(`Server error: ${errorMsg}`);
                }
                if (axiosError.request) {
                    throw new Error('Cannot connect to backend server. Please make sure the server is running at http://127.0.0.1:5050');
                }
                throw axiosError;
            }

            if (token.isCancellationRequested) {
                return;
            }
            
            progress.report({ increment: 95, message: 'Finalizing... (95%)' });
            await new Promise(resolve => setTimeout(resolve, 200));

            if (response.data.ok) {
                progress.report({ increment: 100, message: 'Done! (100%)' });
                
                const explanation = response.data.answer;
                
                // Show explanation in a hover-like popup or output channel
                vscode.window.showInformationMessage(explanation.substring(0, 200) + (explanation.length > 200 ? '...' : ''), 'View Full Explanation')
                    .then(selection => {
                        if (selection === 'View Full Explanation') {
                            const panel = vscode.window.createWebviewPanel(
                                'codeExplanation',
                                'Code Explanation',
                                vscode.ViewColumn.Beside,
                                { enableScripts: true }
                            );
                            panel.webview.html = getExplanationHTML(explanation);
                        }
                    });
            } else {
                const errorMsg = response.data.error || 'Unknown error';
                throw new Error(errorMsg);
            }
        } catch (error: any) {
            if (token.isCancellationRequested) {
                return;
            }
            const errorMsg = error.message || error.response?.data?.error || 'Unknown error';
            console.error('[explain] Error:', error);
            vscode.window.showErrorMessage(`❌ Failed to explain code: ${errorMsg}`);
        }
    });
}

async function provideHoverTooltip(
    document: vscode.TextDocument,
    position: vscode.Position,
    token: vscode.CancellationToken
): Promise<vscode.Hover | undefined> {
    try {
        const config = vscode.workspace.getConfiguration('codeAssistant');
        const hoverEnabled = config.get<boolean>('enableHoverTooltips', true);
        
        if (!hoverEnabled || token.isCancellationRequested) {
            return undefined;
        }

        // Get the word at cursor position
        const wordRange = document.getWordRangeAtPosition(position);
        if (!wordRange) {
            return undefined;
        }

        const word = document.getText(wordRange);
        
        // Only show tooltip for function/class names (simple heuristic)
        if (word.length < 2 || word.length > 50) {
            return undefined;
        }

        // Get line context
        const line = document.lineAt(position.line);
        const lineText = line.text;

        // Simple check: only show if word looks like a function/class name
        if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(word)) {
            return undefined;
        }

        // Get workspace folder for repo_dir
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders || workspaceFolders.length === 0) {
            return undefined;
        }
        const repoDir = workspaceFolders[0].uri.fsPath;

        // Make API call to explain
        try {
            const response = await axios.post(`${SERVER_URL}/chat`, {
                question: `What does "${word}" do in this context: ${lineText.substring(Math.max(0, wordRange.start.character - 50), Math.min(lineText.length, wordRange.end.character + 50))}`,
                repo_dir: repoDir,
                analysis_type: "explain"
            }, {
                timeout: 10000  // 10 second timeout for hover
            });

            if (response.data.ok && response.data.answer) {
                const explanation = response.data.answer.substring(0, 300); // Limit hover text
                return new vscode.Hover(
                    new vscode.MarkdownString(`**AI Explanation:**\n\n${explanation}`),
                    wordRange
                );
            }
        } catch (error) {
            // Silently fail for hover tooltips - don't show errors
            console.log('[hover] Error fetching explanation:', error);
        }

        return undefined;
    } catch (error) {
        return undefined;
    }
}

function getRefactoringSuggestionsHTMLFromMarkdown(markdown: string): string {
    // Convert markdown to HTML (simple conversion)
    let html = markdown
        .replace(/\n\n/g, '</p><p>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/^### (.*)$/gm, '<h3>$1</h3>')
        .replace(/^## (.*)$/gm, '<h2>$1</h2>')
        .replace(/^# (.*)$/gm, '<h1>$1</h1>');
    
    return `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: var(--vscode-font-family);
            padding: 20px;
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
        }
        h1, h2, h3 {
            color: var(--vscode-textLink-foreground);
            margin-top: 20px;
        }
        pre {
            background-color: var(--vscode-textCodeBlock-background);
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
        }
        code {
            background-color: var(--vscode-textCodeBlock-background);
            padding: 2px 6px;
            border-radius: 3px;
        }
        p {
            line-height: 1.6;
        }
    </style>
</head>
<body>
    <h1>Refactoring Suggestions</h1>
    <div>${html}</div>
</body>
</html>`;
}

function getRefactoringSuggestionsHTML(suggestions: any[]): string {
    const suggestionsHTML = suggestions.map((s, i) => `
        <div style="margin-bottom: 20px; padding: 15px; border: 1px solid var(--vscode-input-border); border-radius: 4px;">
            <h3>Suggestion ${i + 1}: ${s.issue || 'Improvement'}</h3>
            <p><strong>Before:</strong></p>
            <pre><code>${s.before || 'N/A'}</code></pre>
            <p><strong>After:</strong></p>
            <pre><code>${s.after || 'N/A'}</code></pre>
            <p><strong>Benefits:</strong> ${s.benefits || 'N/A'}</p>
        </div>
    `).join('');

    return `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: var(--vscode-font-family);
            padding: 20px;
            color: var(--vscode-foreground);
            background: var(--vscode-editor-background);
        }
        pre {
            background: var(--vscode-textCodeBlock-background);
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
        }
        code {
            color: var(--vscode-textPreformat-foreground);
        }
    </style>
</head>
<body>
    <h2>Refactoring Suggestions</h2>
    ${suggestionsHTML}
</body>
</html>`;
}

function getCodeReviewHTML(reviewReport: string, metadata: any): string {
    // Convert markdown to HTML (enhanced conversion for review report)
    let html = reviewReport
        .replace(/\n\n/g, '</p><p>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/^### (.*)$/gm, '<h3>$1</h3>')
        .replace(/^## (.*)$/gm, '<h2>$1</h2>')
        .replace(/^# (.*)$/gm, '<h1>$1</h1>')
        .replace(/^## 🐛 Bugs Found/gm, '<h2>🐛 Bugs Found</h2>')
        .replace(/^## 🔒 Security Issues/gm, '<h2>🔒 Security Issues</h2>')
        .replace(/^## ⚡ Performance Issues/gm, '<h2>⚡ Performance Issues</h2>')
        .replace(/^## 📋 Code Quality Issues/gm, '<h2>📋 Code Quality Issues</h2>')
        .replace(/^## ✅ Positive Observations/gm, '<h2>✅ Positive Observations</h2>')
        .replace(/^## 📊 Summary/gm, '<h2>📊 Summary</h2>');
    
    // Add summary badge if available
    let summaryBadge = '';
    if (metadata?.summary) {
        const summary = metadata.summary;
        const totalIssues = summary.total_issues || 0;
        const criticalHigh = summary.critical_high || 0;
        const overallQuality = summary.overall_quality || 'Unknown';
        
        let qualityColor = 'var(--vscode-textLink-foreground)';
        if (overallQuality.includes('Excellent')) qualityColor = '#4CAF50';
        else if (overallQuality.includes('Good')) qualityColor = '#2196F3';
        else if (overallQuality.includes('Fair')) qualityColor = '#FF9800';
        else if (overallQuality.includes('Needs Improvement') || overallQuality.includes('Poor')) qualityColor = '#F44336';
        
        summaryBadge = `
            <div style="background: var(--vscode-editorWidget-background); padding: 15px; border-radius: 8px; margin-bottom: 20px; border: 1px solid var(--vscode-input-border);">
                <h3 style="margin-top: 0;">Review Summary</h3>
                <div style="display: flex; gap: 20px; flex-wrap: wrap;">
                    <div><strong>Total Issues:</strong> <span style="color: ${criticalHigh > 0 ? '#F44336' : '#4CAF50'}">${totalIssues}</span></div>
                    <div><strong>Critical/High:</strong> <span style="color: ${criticalHigh > 0 ? '#F44336' : '#4CAF50'}">${criticalHigh}</span></div>
                    <div><strong>Overall Quality:</strong> <span style="color: ${qualityColor}">${overallQuality}</span></div>
                </div>
            </div>
        `;
    }
    
    return `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: var(--vscode-font-family);
            padding: 20px;
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
            line-height: 1.6;
        }
        h1, h2, h3 {
            color: var(--vscode-textLink-foreground);
            margin-top: 20px;
        }
        h2 {
            border-bottom: 2px solid var(--vscode-input-border);
            padding-bottom: 5px;
        }
        pre {
            background-color: var(--vscode-textCodeBlock-background);
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
            border: 1px solid var(--vscode-input-border);
        }
        code {
            background-color: var(--vscode-textCodeBlock-background);
            padding: 2px 6px;
            border-radius: 3px;
            font-family: var(--vscode-editor-font-family);
        }
        p {
            line-height: 1.6;
            margin: 10px 0;
        }
        ul, ol {
            margin: 10px 0;
            padding-left: 30px;
        }
        li {
            margin: 5px 0;
        }
        strong {
            color: var(--vscode-textLink-foreground);
        }
    </style>
</head>
<body>
    <h1>Code Review Report</h1>
    ${summaryBadge}
    <div>${html}</div>
</body>
</html>`;
}

function getExplanationHTML(explanation: string): string {
    return `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: var(--vscode-font-family);
            padding: 20px;
            color: var(--vscode-foreground);
            background: var(--vscode-editor-background);
            line-height: 1.6;
        }
        pre {
            background: var(--vscode-textCodeBlock-background);
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
        }
        code {
            color: var(--vscode-textPreformat-foreground);
        }
    </style>
</head>
<body>
    <h2>Code Explanation</h2>
    <div style="white-space: pre-wrap;">${explanation.replace(/\n/g, '<br>')}</div>
</body>
</html>`;
}

export function deactivate() {}

