/**
 * Status bar integration for authentication.
 * Shows login state and provides quick access to auth commands.
 */
import * as vscode from 'vscode';
import { isAuthenticated, getUsername } from './auth';

let statusBarItem: vscode.StatusBarItem | undefined;
let signupStatusBarItem: vscode.StatusBarItem | undefined;

/**
 * Create and show authentication status bar item.
 */
export function createAuthStatusBar(context: vscode.ExtensionContext) {
    // Create login status bar item with higher priority to ensure visibility
    statusBarItem = vscode.window.createStatusBarItem(
        vscode.StatusBarAlignment.Right,
        200  // Higher priority to ensure it's visible
    );
    
    // Create signup status bar item
    signupStatusBarItem = vscode.window.createStatusBarItem(
        vscode.StatusBarAlignment.Right,
        199  // Slightly lower priority than login
    );
    
    // Initial update
    updateAuthStatusBar(context);
    
    // Update when auth state changes
    context.subscriptions.push(
        vscode.commands.registerCommand('codeAssistant.refreshAuth', () => {
            updateAuthStatusBar(context);
        })
    );
    
    // Show status bars immediately
    statusBarItem.show();
    if (signupStatusBarItem) {
        signupStatusBarItem.show();
    }
    
    // Add to subscriptions for cleanup
    context.subscriptions.push(statusBarItem);
    if (signupStatusBarItem) {
        context.subscriptions.push(signupStatusBarItem);
    }
    
    return statusBarItem;
}

/**
 * Update the authentication status bar display.
 */
export async function updateAuthStatusBar(context: vscode.ExtensionContext) {
    if (!statusBarItem) {
        return;
    }
    
    const authenticated = await isAuthenticated(context);
    
    if (authenticated) {
        const username = await getUsername(context) || 'User';
        statusBarItem.text = `$(account) ${username}`;
        statusBarItem.command = 'codeAssistant.profile';
        statusBarItem.tooltip = `Logged in as ${username}. Click to view profile or use command palette to logout.`;
        // Hide signup button when logged in
        if (signupStatusBarItem) {
            signupStatusBarItem.hide();
        }
    } else {
        // Show login button
        statusBarItem.text = '$(sign-in) Login';
        statusBarItem.command = 'codeAssistant.login';
        statusBarItem.tooltip = 'Click to login. You need to login to use Code Assistant features.';
        statusBarItem.show();
        
        // Show signup button
        if (signupStatusBarItem) {
            signupStatusBarItem.text = '$(account) Sign Up';
            signupStatusBarItem.command = 'codeAssistant.signup';
            signupStatusBarItem.tooltip = 'Click to create a new account';
            signupStatusBarItem.show();
        }
    }
}

/**
 * Dispose of status bar item.
 */
export function disposeAuthStatusBar() {
    if (statusBarItem) {
        statusBarItem.dispose();
        statusBarItem = undefined;
    }
    if (signupStatusBarItem) {
        signupStatusBarItem.dispose();
        signupStatusBarItem = undefined;
    }
}

