/**
 * Authentication JavaScript
 * Handles login, registration, and token management
 */

const API_BASE = 'http://127.0.0.1:5050';

// Token management
const TokenManager = {
    getToken() {
        return localStorage.getItem('authToken');
    },
    
    setToken(token) {
        localStorage.setItem('authToken', token);
    },
    
    removeToken() {
        localStorage.removeItem('authToken');
        localStorage.removeItem('username');
        localStorage.removeItem('userId');
    },
    
    setUserInfo(user) {
        if (user) {
            localStorage.setItem('username', user.username || '');
            localStorage.setItem('userId', user.id?.toString() || '');
        }
    },
    
    getUserInfo() {
        return {
            username: localStorage.getItem('username'),
            userId: localStorage.getItem('userId'),
            token: this.getToken()
        };
    },
    
    isAuthenticated() {
        return !!this.getToken();
    }
};

// API helper
async function apiCall(endpoint, options = {}) {
    const token = TokenManager.getToken();
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    try {
        const url = `${API_BASE}${endpoint}`;
        console.log('[apiCall] Making request to:', url, options.method || 'GET');
        console.log('[apiCall] Request options:', { method: options.method || 'GET', headers, body: options.body });
        
        const fetchOptions = {
            method: options.method || 'GET',
            headers: headers,
            mode: 'cors',
            credentials: 'omit'
        };
        
        if (options.body) {
            fetchOptions.body = options.body;
        }
        
        console.log('[apiCall] Fetch options:', fetchOptions);
        
        const response = await fetch(url, fetchOptions);
        
        console.log('[apiCall] Response status:', response.status, response.statusText);
        
        let data;
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            data = await response.json();
        } else {
            const text = await response.text();
            console.error('[apiCall] Non-JSON response:', text);
            return {
                ok: false,
                status: response.status,
                error: `Server returned non-JSON response: ${text.substring(0, 100)}`
            };
        }
        
        console.log('[apiCall] Response data:', data);
        
        return {
            ok: response.ok,
            status: response.status,
            data
        };
    } catch (error) {
        console.error('[apiCall] Error:', error);
        return {
            ok: false,
            status: 0,
            error: error.message
        };
    }
}

// Form validation
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePassword(password) {
    return password.length >= 6;
}

function validateUsername(username) {
    return username.length >= 3;
}

function showError(elementId, message) {
    const errorEl = document.getElementById(elementId);
    if (errorEl) {
        errorEl.textContent = message;
        errorEl.style.display = 'block';
    }
}

function clearError(elementId) {
    const errorEl = document.getElementById(elementId);
    if (errorEl) {
        errorEl.textContent = '';
        errorEl.style.display = 'none';
    }
}

function showMessage(message, type = 'success') {
    const messageEl = document.getElementById('authMessage');
    if (messageEl) {
        messageEl.textContent = message;
        messageEl.className = `auth-message ${type}`;
        messageEl.style.display = 'block';
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            messageEl.style.display = 'none';
        }, 5000);
    }
}

function setLoading(form, loading) {
    const submitBtn = form.querySelector('button[type="submit"]');
    const btnText = submitBtn.querySelector('.btn-text');
    const btnLoader = submitBtn.querySelector('.btn-loader');
    
    if (loading) {
        submitBtn.disabled = true;
        btnText.style.display = 'none';
        btnLoader.style.display = 'inline-block';
        form.classList.add('loading');
    } else {
        submitBtn.disabled = false;
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
        form.classList.remove('loading');
    }
}

// Login form handler
const loginForm = document.getElementById('loginForm');
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Clear previous errors
        clearError('usernameError');
        clearError('passwordError');
        
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;
        
        // Validation
        if (!username) {
            showError('usernameError', 'Username or email is required');
            return;
        }
        
        if (!password) {
            showError('passwordError', 'Password is required');
            return;
        }
        
        setLoading(loginForm, true);
        
        try {
            const result = await apiCall('/auth/login', {
                method: 'POST',
                body: JSON.stringify({
                    username_or_email: username,
                    password: password
                })
            });
            
            if (result.ok && result.data.ok) {
                // Store token and user info
                TokenManager.setToken(result.data.token);
                TokenManager.setUserInfo(result.data.user);
                
                showMessage('Login successful! Redirecting...', 'success');
                
                // Redirect to main app after 1 second
                setTimeout(() => {
                    window.location.href = '/';
                }, 1000);
            } else {
                const errorMsg = result.data?.error || 'Login failed. Please check your credentials.';
                showMessage(errorMsg, 'error');
                
                if (result.status === 401) {
                    showError('passwordError', 'Invalid username or password');
                }
            }
        } catch (error) {
            showMessage('Network error. Please check if the server is running.', 'error');
        } finally {
            setLoading(loginForm, false);
        }
    });
}

// Register form handler
const registerForm = document.getElementById('registerForm');
if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Clear previous errors
        clearError('regUsernameError');
        clearError('regEmailError');
        clearError('regPasswordError');
        clearError('regConfirmPasswordError');
        
        const username = document.getElementById('regUsername').value.trim();
        const email = document.getElementById('regEmail').value.trim();
        const password = document.getElementById('regPassword').value;
        const confirmPassword = document.getElementById('regConfirmPassword').value;
        
        // Validation
        let hasErrors = false;
        
        if (!validateUsername(username)) {
            showError('regUsernameError', 'Username must be at least 3 characters');
            hasErrors = true;
        }
        
        if (!validateEmail(email)) {
            showError('regEmailError', 'Please enter a valid email address');
            hasErrors = true;
        }
        
        if (!validatePassword(password)) {
            showError('regPasswordError', 'Password must be at least 6 characters');
            hasErrors = true;
        }
        
        if (password !== confirmPassword) {
            showError('regConfirmPasswordError', 'Passwords do not match');
            hasErrors = true;
        }
        
        if (hasErrors) {
            return;
        }
        
        setLoading(registerForm, true);
        
        try {
            console.log('[register] Submitting registration:', { username, email });
            
            const result = await apiCall('/auth/register', {
                method: 'POST',
                body: JSON.stringify({
                    username: username,
                    email: email,
                    password: password
                })
            });
            
            console.log('[register] Registration result:', result);
            
            if (result.ok && result.data && result.data.ok) {
                showMessage('Account created successfully! Logging you in...', 'success');
                
                // Auto-login after registration
                const loginResult = await apiCall('/auth/login', {
                    method: 'POST',
                    body: JSON.stringify({
                        username_or_email: username,
                        password: password
                    })
                });
                
                if (loginResult.ok && loginResult.data.ok) {
                    TokenManager.setToken(loginResult.data.token);
                    TokenManager.setUserInfo(loginResult.data.user);
                    
                    // Redirect to main app
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 1500);
                } else {
                    showMessage('Account created! Please login.', 'success');
                    setTimeout(() => {
                        window.location.href = '/login';
                    }, 2000);
                }
            } else {
                const errorMsg = result.data?.error || result.error || 'Registration failed';
                console.error('[register] Registration failed:', errorMsg, result);
                showMessage(errorMsg, 'error');
                
                // Show specific field errors
                if (errorMsg.includes('username')) {
                    showError('regUsernameError', errorMsg);
                } else if (errorMsg.includes('email')) {
                    showError('regEmailError', errorMsg);
                } else if (errorMsg.includes('password')) {
                    showError('regPasswordError', errorMsg);
                }
            }
        } catch (error) {
            console.error('[register] Exception:', error);
            showMessage(`Network error: ${error.message}. Please check if the server is running.`, 'error');
        } finally {
            setLoading(registerForm, false);
        }
    });
}

// Password visibility toggle
function setupPasswordToggles() {
    const toggles = document.querySelectorAll('.toggle-password');
    toggles.forEach(toggle => {
        // Completely clear button - remove ALL children
        while (toggle.firstChild) {
            toggle.removeChild(toggle.firstChild);
        }
        
        // Create a single icon element
        const eyeIcon = document.createElement('span');
        eyeIcon.className = 'eye-icon';
        eyeIcon.setAttribute('aria-hidden', 'true');
        toggle.appendChild(eyeIcon);
        
        // Get the input field
        const input = toggle.parentElement.querySelector('input');
        if (input) {
            // Set initial icon - closed eye when password is hidden
            if (input.type === 'password') {
                eyeIcon.textContent = '🙈';
            } else {
                eyeIcon.textContent = '👁';
            }
        }
        
        // Remove any existing listeners by cloning
        const newToggle = toggle.cloneNode(false);
        newToggle.className = toggle.className;
        newToggle.id = toggle.id;
        newToggle.setAttribute('aria-label', toggle.getAttribute('aria-label') || 'Toggle password');
        newToggle.appendChild(eyeIcon);
        toggle.parentNode.replaceChild(newToggle, toggle);
        
        newToggle.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            const input = newToggle.parentElement.querySelector('input');
            const icon = newToggle.querySelector('.eye-icon');
            
            if (!input || !icon) return;
            
            if (input.type === 'password') {
                // Show password - change to text input
                input.type = 'text';
                // Show open eye (password is now visible)
                icon.textContent = '👁';
                newToggle.setAttribute('aria-label', 'Hide password');
            } else {
                // Hide password - change to password input
                input.type = 'password';
                // Show closed eye (password is now hidden)
                icon.textContent = '🙈';
                newToggle.setAttribute('aria-label', 'Show password');
            }
        });
    });
}

// Real-time validation
function setupRealTimeValidation() {
    // Username validation
    const regUsername = document.getElementById('regUsername');
    if (regUsername) {
        regUsername.addEventListener('input', () => {
            const value = regUsername.value.trim();
            if (value && !validateUsername(value)) {
                showError('regUsernameError', 'Username must be at least 3 characters');
            } else {
                clearError('regUsernameError');
            }
        });
    }
    
    // Email validation
    const regEmail = document.getElementById('regEmail');
    if (regEmail) {
        regEmail.addEventListener('input', () => {
            const value = regEmail.value.trim();
            if (value && !validateEmail(value)) {
                showError('regEmailError', 'Please enter a valid email address');
            } else {
                clearError('regEmailError');
            }
        });
    }
    
    // Password validation
    const regPassword = document.getElementById('regPassword');
    if (regPassword) {
        regPassword.addEventListener('input', () => {
            const value = regPassword.value;
            if (value && !validatePassword(value)) {
                showError('regPasswordError', 'Password must be at least 6 characters');
            } else {
                clearError('regPasswordError');
            }
        });
    }
    
    // Confirm password validation
    const regConfirmPassword = document.getElementById('regConfirmPassword');
    const regPasswordInput = document.getElementById('regPassword');
    if (regConfirmPassword && regPasswordInput) {
        regConfirmPassword.addEventListener('input', () => {
            const password = regPasswordInput.value;
            const confirm = regConfirmPassword.value;
            if (confirm && password !== confirm) {
                showError('regConfirmPasswordError', 'Passwords do not match');
            } else {
                clearError('regConfirmPasswordError');
            }
        });
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Initialize password toggles first
    setupPasswordToggles();
    setupRealTimeValidation();
    
    // Check if already logged in
    if (TokenManager.isAuthenticated()) {
        // Verify token is still valid
        apiCall('/auth/me').then(result => {
            if (!result.ok) {
                // Token invalid, clear it
                TokenManager.removeToken();
            } else {
                // Already logged in, redirect to home
                if (window.location.pathname.includes('login.html') || 
                    window.location.pathname.includes('register.html')) {
                    window.location.href = '/';
                }
            }
        });
    }
});

// Export for use in other scripts
window.TokenManager = TokenManager;
window.apiCall = apiCall;

