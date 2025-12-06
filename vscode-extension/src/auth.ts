/**
 * Authentication module for VS Code extension.
 * Handles user login, signup, and token management.
 */
import * as vscode from 'vscode';
import axios from 'axios';
import { promptLanguageSelection } from './i18n';

const API_BASE = 'http://127.0.0.1:5050';

/**
 * Register a new user account.
 */
export async function signup(context: vscode.ExtensionContext) {
    try {
        // Get username
        const username = await vscode.window.showInputBox({
            prompt: 'Choose a username',
            placeHolder: 'Enter your username (min 3 characters)',
            validateInput: (value) => {
                if (!value || value.length < 3) {
                    return 'Username must be at least 3 characters';
                }
                return null;
            }
        });
        
        if (!username) {
            return; // User cancelled
        }
        
        // Get email
        const email = await vscode.window.showInputBox({
            prompt: 'Enter your email address',
            placeHolder: 'your.email@example.com',
            validateInput: (value) => {
                if (!value || !value.includes('@')) {
                    return 'Please enter a valid email address';
                }
                return null;
            }
        });
        
        if (!email) {
            return; // User cancelled
        }
        
        // Get password
        const password = await vscode.window.showInputBox({
            prompt: 'Choose a password',
            placeHolder: 'Enter your password (min 6 characters)',
            password: true,
            validateInput: (value) => {
                if (!value || value.length < 6) {
                    return 'Password must be at least 6 characters';
                }
                return null;
            }
        });
        
        if (!password) {
            return; // User cancelled
        }
        
        // Confirm password
        const confirmPassword = await vscode.window.showInputBox({
            prompt: 'Confirm your password',
            placeHolder: 'Re-enter your password',
            password: true,
            validateInput: (value) => {
                if (value !== password) {
                    return 'Passwords do not match';
                }
                return null;
            }
        });
        
        if (!confirmPassword) {
            return; // User cancelled
        }
        
        // Show progress
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Creating account...",
            cancellable: false
        }, async () => {
            try {
                // Call registration API
                const response = await axios.post(`${API_BASE}/auth/register`, {
                    username: username,
                    email: email,
                    password: password
                });
                
                if (response.data.ok) {
                    // Auto-login after successful registration
                    const loginResponse = await axios.post(`${API_BASE}/auth/login`, {
                        username_or_email: username,
                        password: password
                    });
                    
                    if (loginResponse.data.ok) {
                        // Store token and user info
                        await context.secrets.store('authToken', loginResponse.data.token);
                        await context.secrets.store('username', loginResponse.data.user.username);
                        await context.secrets.store('userId', loginResponse.data.user.id.toString());
                        
                        vscode.window.showInformationMessage(
                            `✅ Account created and logged in as ${loginResponse.data.user.username}`
                        );
                        
                        // Prompt for language selection after signup
                        await promptLanguageSelection(context);
                        
                        // Refresh auth status
                        vscode.commands.executeCommand('codeAssistant.refreshAuth');
                    } else {
                        vscode.window.showWarningMessage(
                            'Account created but auto-login failed. Please login manually.'
                        );
                    }
                } else {
                    vscode.window.showErrorMessage(
                        `Registration failed: ${response.data.error || 'Unknown error'}`
                    );
                }
            } catch (error: any) {
                const errorMessage = error.response?.data?.error || error.message || 'Unknown error';
                vscode.window.showErrorMessage(`Registration failed: ${errorMessage}`);
            }
        });
    } catch (error: any) {
        vscode.window.showErrorMessage(`Signup failed: ${error.message}`);
    }
}

/**
 * Login with username/email and password.
 */
export async function login(context: vscode.ExtensionContext) {
    try {
        // Get username or email
        const usernameOrEmail = await vscode.window.showInputBox({
            prompt: 'Enter your username or email',
            placeHolder: 'username or email@example.com'
        });
        
        if (!usernameOrEmail) {
            return; // User cancelled
        }
        
        // Get password
        const password = await vscode.window.showInputBox({
            prompt: 'Enter your password',
            placeHolder: 'Enter your password',
            password: true
        });
        
        if (!password) {
            return; // User cancelled
        }
        
        // Show progress
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Logging in...",
            cancellable: false
        }, async () => {
            try {
                // Call login API
                const response = await axios.post(`${API_BASE}/auth/login`, {
                    username_or_email: usernameOrEmail,
                    password: password
                });
                
                if (response.data.ok) {
                    // Store token and user info
                    await context.secrets.store('authToken', response.data.token);
                    await context.secrets.store('username', response.data.user.username);
                    await context.secrets.store('userId', response.data.user.id.toString());
                    
                    vscode.window.showInformationMessage(
                        `✅ Logged in as ${response.data.user.username}`
                    );
                    
                    // Prompt for language selection after login (if not already set)
                    await promptLanguageSelection(context);
                    
                    // Refresh auth status
                    vscode.commands.executeCommand('codeAssistant.refreshAuth');
                } else {
                    vscode.window.showErrorMessage(
                        `Login failed: ${response.data.error || 'Invalid credentials'}`
                    );
                }
            } catch (error: any) {
                const errorMessage = error.response?.data?.error || error.message || 'Unknown error';
                vscode.window.showErrorMessage(`Login failed: ${errorMessage}`);
            }
        });
    } catch (error: any) {
        vscode.window.showErrorMessage(`Login failed: ${error.message}`);
    }
}

/**
 * Logout current user.
 */
export async function logout(context: vscode.ExtensionContext) {
    try {
        // Clear stored credentials
        await context.secrets.delete('authToken');
        await context.secrets.delete('username');
        await context.secrets.delete('userId');
        
        vscode.window.showInformationMessage('✅ Logged out successfully');
        
        // Refresh auth status
        vscode.commands.executeCommand('codeAssistant.refreshAuth');
    } catch (error: any) {
        vscode.window.showErrorMessage(`Logout failed: ${error.message}`);
    }
}

/**
 * Get current authentication token.
 */
export async function getAuthToken(context: vscode.ExtensionContext): Promise<string | undefined> {
    return await context.secrets.get('authToken');
}

/**
 * Get current username.
 */
export async function getUsername(context: vscode.ExtensionContext): Promise<string | undefined> {
    return await context.secrets.get('username');
}

/**
 * Get current user ID.
 */
export async function getUserId(context: vscode.ExtensionContext): Promise<number | undefined> {
    const userIdStr = await context.secrets.get('userId');
    return userIdStr ? parseInt(userIdStr, 10) : undefined;
}

/**
 * Check if user is authenticated.
 */
export async function isAuthenticated(context: vscode.ExtensionContext): Promise<boolean> {
    const token = await getAuthToken(context);
    return !!token;
}

/**
 * Get authentication headers for API requests.
 */
export async function getAuthHeaders(context: vscode.ExtensionContext): Promise<Record<string, string>> {
    const token = await getAuthToken(context);
    if (token) {
        return {
            'Authorization': `Bearer ${token}`
        };
    }
    return {};
}

/**
 * Verify current token is still valid.
 */
export async function verifyToken(context: vscode.ExtensionContext): Promise<boolean> {
    try {
        const token = await getAuthToken(context);
        if (!token) {
            return false;
        }
        
        const headers = await getAuthHeaders(context);
        const response = await axios.get(`${API_BASE}/auth/me`, { headers });
        
        return response.data.ok === true;
    } catch (error) {
        // Token is invalid or expired
        await logout(context);
        return false;
    }
}

/**
 * Show user profile information.
 */
export async function showProfile(context: vscode.ExtensionContext) {
    try {
        const isAuth = await isAuthenticated(context);
        if (!isAuth) {
            const action = await vscode.window.showInformationMessage(
                'You are not logged in. Would you like to login?',
                'Login',
                'Signup'
            );
            
            if (action === 'Login') {
                await login(context);
            } else if (action === 'Signup') {
                await signup(context);
            }
            return;
        }
        
        // Verify token first
        const isValid = await verifyToken(context);
        if (!isValid) {
            vscode.window.showErrorMessage('Your session has expired. Please login again.');
            return;
        }
        
        // Get user info
        const headers = await getAuthHeaders(context);
        const response = await axios.get(`${API_BASE}/auth/me`, { headers });
        
        if (response.data.ok) {
            const user = response.data.user;
            const message = [
                `Username: ${user.username}`,
                `Email: ${user.email}`,
                `Account created: ${new Date(user.created_at).toLocaleDateString()}`
            ].join('\n');
            
            vscode.window.showInformationMessage(message);
        } else {
            vscode.window.showErrorMessage('Failed to fetch user profile');
        }
    } catch (error: any) {
        vscode.window.showErrorMessage(`Failed to show profile: ${error.message}`);
    }
}

