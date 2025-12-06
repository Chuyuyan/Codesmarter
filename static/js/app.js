// Note: auth.js is loaded before this script in index.html
// TokenManager, apiCall, and API_BASE should be available from window
// Don't redeclare API_BASE - use the one from auth.js

// Check authentication on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('[app] DOMContentLoaded - Starting auth check');
    console.log('[app] Document ready state:', document.readyState);
    // Wait for TokenManager and apiCall to be available
    setTimeout(() => {
        console.log('[app] Running checkAuthStatus after delay');
        checkAuthStatus();
        setupAuthUI();
    }, 500);
});

// Also check when window loads (in case DOMContentLoaded already fired)
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('[app] DOM was loading, added listener');
        setTimeout(() => {
            console.log('[app] Running checkAuthStatus from loading state');
            checkAuthStatus();
        }, 500);
    });
} else {
    // DOM already loaded
    console.log('[app] DOM already loaded, running checkAuthStatus immediately');
    setTimeout(() => {
        console.log('[app] Running checkAuthStatus from ready state');
        checkAuthStatus();
    }, 500);
}

function checkAuthStatus() {
    console.log('[app] checkAuthStatus called');
    
    // Wait for both TokenManager and apiCall to be available
    if (typeof TokenManager === 'undefined' || typeof apiCall === 'undefined') {
        console.log('[app] Waiting for TokenManager or apiCall, retrying...', {
            hasTokenManager: typeof TokenManager !== 'undefined',
            hasApiCall: typeof apiCall !== 'undefined'
        });
        setTimeout(checkAuthStatus, 100);
        return;
    }
    
    const hasToken = TokenManager.isAuthenticated();
    console.log('[app] Token check:', { hasToken, token: hasToken ? 'exists' : 'missing' });
    
    if (hasToken) {
        const token = TokenManager.getToken();
        console.log('[app] Token found, verifying with /auth/me');
        console.log('[app] Token (first 20 chars):', token ? token.substring(0, 20) + '...' : 'null');
        
        // Verify token is still valid
        apiCall('/auth/me').then(result => {
            console.log('[app] /auth/me response status:', result.status);
            console.log('[app] /auth/me response ok:', result.ok);
            console.log('[app] /auth/me response data:', result.data);
            
            if (result.ok && result.data && result.data.ok) {
                console.log('[app] ✅ Auth verified, user:', result.data.user);
                console.log('[app] Calling updateAuthUI...');
                updateAuthUI(result.data.user);
                console.log('[app] updateAuthUI completed');
            } else {
                console.warn('[app] ❌ Token invalid, clearing');
                console.warn('[app] Response details:', {
                    ok: result.ok,
                    status: result.status,
                    data: result.data,
                    error: result.error
                });
                // Token invalid, clear it
                TokenManager.removeToken();
                const authButtons = document.getElementById('authButtons');
                if (authButtons) {
                    authButtons.style.display = 'none';
                }
                // Don't redirect - allow user to stay on page
            }
        }).catch((error) => {
            console.error('[app] ❌ Error checking auth:', error);
            console.error('[app] Error stack:', error.stack);
            // Error checking auth - hide buttons but don't redirect
            const authButtons = document.getElementById('authButtons');
            if (authButtons) {
                authButtons.style.display = 'none';
            }
        });
    } else {
        console.log('[app] No token found, hiding auth buttons');
        // Not authenticated - hide buttons
        const authButtons = document.getElementById('authButtons');
        if (authButtons) {
            authButtons.style.display = 'none';
        }
    }
}

function setupAuthUI() {
    // Setup logout button in navbar
    const logoutBtn = document.getElementById('logoutBtn');
    
    function handleLogout() {
        if (typeof TokenManager !== 'undefined') {
            TokenManager.removeToken();
        }
        window.location.href = '/login';
    }
    
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }
}

function updateAuthUI(user) {
    console.log('[app] updateAuthUI called with user:', user);
    
    // Update navbar auth buttons - show My Account and Logout
    const authButtons = document.getElementById('authButtons');
    console.log('[app] authButtons element:', authButtons);
    console.log('[app] authButtons before change - display:', authButtons ? window.getComputedStyle(authButtons).display : 'N/A');
    
    if (authButtons) {
        console.log('[app] Setting authButtons display to flex...');
        // Force remove inline style that might be hiding it
        authButtons.removeAttribute('style');
        // Set display to flex with all necessary styles
        authButtons.style.cssText = 'display: flex !important; gap: 12px; align-items: center;';
        console.log('[app] ✅ Auth buttons display set. Computed style:', window.getComputedStyle(authButtons).display);
        console.log('[app] Auth buttons innerHTML:', authButtons.innerHTML);
        console.log('[app] Auth buttons children count:', authButtons.children.length);
        
        // Also check if buttons inside are visible
        const accountBtn = authButtons.querySelector('a[href="/account"]');
        const logoutBtn = authButtons.querySelector('#logoutBtn');
        console.log('[app] Account button:', accountBtn);
        console.log('[app] Logout button:', logoutBtn);
    } else {
        console.error('[app] ❌ authButtons element not found!');
        const navbarRight = document.querySelector('.navbar-right');
        console.error('[app] navbar-right element:', navbarRight);
        console.error('[app] navbar-right innerHTML:', navbarRight?.innerHTML);
    }
    
    // Legacy auth status bar removed - using top navbar instead
}

// Helper function to get auth headers
function getAuthHeaders() {
    const headers = {
        'Content-Type': 'application/json'
    };
    
    if (typeof TokenManager !== 'undefined' && TokenManager.isAuthenticated()) {
        headers['Authorization'] = `Bearer ${TokenManager.getToken()}`;
    }
    
    return headers;
}

// Helper function to show status messages
function showStatus(elementId, message, type) {
    const statusEl = document.getElementById(elementId);
    statusEl.textContent = message;
    statusEl.className = `status ${type}`;
    statusEl.style.display = 'block';
}

// Helper function to hide status
function hideStatus(elementId) {
    const statusEl = document.getElementById(elementId);
    statusEl.style.display = 'none';
}

// Index repository
document.getElementById('index-btn').addEventListener('click', async () => {
    const repoDir = document.getElementById('repo-dir').value.trim();
    if (!repoDir) {
        showStatus('index-status', 'Please enter a repository path', 'error');
        return;
    }

    const btn = document.getElementById('index-btn');
    btn.disabled = true;
    showStatus('index-status', 'Indexing repository... This may take a few minutes.', 'loading');

    try {
        const apiBase = (typeof API_BASE !== 'undefined' ? API_BASE : 'http://127.0.0.1:5050');
        const response = await fetch(`${apiBase}/index_repo`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ repo_dir: repoDir })
        });

        const data = await response.json();

        if (data.ok) {
            showStatus('index-status', 
                `✅ Successfully indexed! Found ${data.chunks} chunks. Repository ID: ${data.repo_id}`, 
                'success');
        } else {
            showStatus('index-status', `❌ Error: ${data.error}`, 'error');
        }
    } catch (error) {
        showStatus('index-status', `❌ Network error: ${error.message}`, 'error');
    } finally {
        btn.disabled = false;
    }
});

// Setup auto-detect mode toggle
document.addEventListener('DOMContentLoaded', () => {
    const autoDetectCheckbox = document.getElementById('auto-detect-mode');
    const analysisTypeSelect = document.getElementById('analysis-type');
    
    if (autoDetectCheckbox && analysisTypeSelect) {
        // Toggle dropdown visibility based on checkbox
        autoDetectCheckbox.addEventListener('change', (e) => {
            const isAuto = e.target.checked;
            analysisTypeSelect.style.display = isAuto ? 'none' : 'block';
        });
        
        // Set initial state
        analysisTypeSelect.style.display = autoDetectCheckbox.checked ? 'none' : 'block';
    }
});

// Add language selection UI to generation (if we add a generate section)
// For now, chat will auto-detect language from existing code

// Chat / Ask question
document.getElementById('chat-btn').addEventListener('click', async () => {
    const repoDir = document.getElementById('chat-repo-dir').value.trim();
    const question = document.getElementById('question').value.trim();
    const autoDetectCheckbox = document.getElementById('auto-detect-mode');
    const analysisTypeSelect = document.getElementById('analysis-type');
    
    // Determine analysis type: auto-detect if checkbox is checked, otherwise use manual selection
    const useAutoDetect = autoDetectCheckbox ? autoDetectCheckbox.checked : true;
    const selectedAnalysisType = useAutoDetect ? null : (analysisTypeSelect ? analysisTypeSelect.value : null);

    if (!repoDir || !question) {
        showStatus('chat-status', 'Please enter both repository path and question', 'error');
        return;
    }

    const btn = document.getElementById('chat-btn');
    btn.disabled = true;
    hideStatus('chat-status');
    showStatus('chat-status', 'Analyzing code and generating answer...', 'loading');
    
    // Show results section
    document.getElementById('results-section').style.display = 'block';
    document.getElementById('answer').textContent = 'Loading...';
    document.getElementById('citations').innerHTML = '';

    try {
        const apiBase = typeof API_BASE !== 'undefined' ? API_BASE : 'http://127.0.0.1:5050';
        
        // Build request body - only include analysis_type if manually selected
        const requestBody = {
            repo_dir: repoDir,
            question: question
        };
        
        // Only include analysis_type if manually selected
        if (!useAutoDetect && selectedAnalysisType) {
            requestBody.analysis_type = selectedAnalysisType;
        }
        // If autoDetect is true, backend will automatically detect the analysis type
        
        const response = await fetch(`${apiBase}/chat`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(requestBody)
        });

        const data = await response.json();

        if (data.ok) {
            // Display answer
            const answerEl = document.getElementById('answer');
            answerEl.textContent = data.answer;
            
            // Format answer (basic markdown support)
            answerEl.innerHTML = formatMarkdown(data.answer);

            // Display citations
            const citationsEl = document.getElementById('citations');
            if (data.citations && data.citations.length > 0) {
                citationsEl.innerHTML = data.citations.map(citation => `
                    <div class="citation-item">
                        <div class="file">📄 ${citation.file.split('\\').pop().split('/').pop()}</div>
                        <div class="lines">Lines ${citation.start}-${citation.end}</div>
                    </div>
                `).join('');
            } else {
                citationsEl.innerHTML = '<p>No citations available</p>';
            }

            hideStatus('chat-status');
            showStatus('chat-status', '✅ Answer generated successfully!', 'success');
        } else {
            document.getElementById('answer').textContent = `Error: ${data.error}`;
            hideStatus('chat-status');
            showStatus('chat-status', `❌ Error: ${data.error}`, 'error');
        }
    } catch (error) {
        document.getElementById('answer').textContent = `Network error: ${error.message}`;
        hideStatus('chat-status');
        showStatus('chat-status', `❌ Network error: ${error.message}`, 'error');
    } finally {
        btn.disabled = false;
    }
});

// Simple markdown formatting
function formatMarkdown(text) {
    // Code blocks
    text = text.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    // Inline code
    text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
    // Bold
    text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    // Headers
    text = text.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    text = text.replace(/^## (.+)$/gm, '<h2>$1</h2>');
    text = text.replace(/^# (.+)$/gm, '<h1>$1</h1>');
    // Line breaks
    text = text.replace(/\n/g, '<br>');
    return text;
}

// Allow Enter key to submit (Ctrl+Enter for chat)
document.getElementById('question').addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && e.ctrlKey) {
        document.getElementById('chat-btn').click();
    }
});

