#!/bin/bash
# Script to fix auth.js directly in Docker container

echo "Fixing auth.js in Docker container..."

docker exec smartcursor bash -c 'cat > /app/static/js/auth.js << '\''EOFAUTH'\''
/**
 * Authentication JavaScript
 * Handles login, registration, and token management
 */

// Auto-detect API base URL based on current page
const API_BASE = (() => {
    // If running on same domain, use relative path (works for Docker/public access)
    if (window.location.hostname !== '\''127.0.0.1'\'' && window.location.hostname !== '\''localhost'\'') {
        // Public access - use same origin
        return '\'''\'';
    }
    // Local development
    return '\''http://127.0.0.1:5050'\'';
})();

// Token management
const TokenManager = {
    getToken() {
        return localStorage.getItem('\''authToken'\'');
    },
    
    setToken(token) {
        localStorage.setItem('\''authToken'\'', token);
    },
    
    removeToken() {
        localStorage.removeItem('\''authToken'\'');
        localStorage.removeItem('\''username'\'');
        localStorage.removeItem('\''userId'\'');
    },
    
    setUserInfo(user) {
        if (user) {
            localStorage.setItem('\''username'\'', user.username || '\'''\'');
            localStorage.setItem('\''userId'\'', user.id?.toString() || '\'''\'');
        }
    },
    
    getUserInfo() {
        return {
            username: localStorage.getItem('\''username'\''),
            userId: localStorage.getItem('\''userId'\''),
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
        '\''Content-Type'\'': '\''application/json'\'',
        ...options.headers
    };
    
    if (token) {
        headers['\''Authorization'\''] = `Bearer ${token}`;
    }
    
    try {
        // Use relative path if API_BASE is empty (same origin), otherwise use full URL
        const url = API_BASE ? `${API_BASE}${endpoint}` : endpoint;
        console.log('\''[apiCall] Making request to:'\'', url, options.method || '\''GET'\'');
        console.log('\''[apiCall] Request options:'\'', { method: options.method || '\''GET'\'', headers, body: options.body });
        
        const fetchOptions = {
            method: options.method || '\''GET'\'',
            headers: headers,
            mode: '\''cors'\'',
            credentials: '\''omit'\''
        };
        
        if (options.body) {
            fetchOptions.body = options.body;
        }
        
        console.log('\''[apiCall] Fetch options:'\'', fetchOptions);
        
        const response = await fetch(url, fetchOptions);
        
        console.log('\''[apiCall] Response status:'\'', response.status, response.statusText);
        
        let data;
        const contentType = response.headers.get('\''content-type'\'');
        if (contentType && contentType.includes('\''application/json'\'')) {
            data = await response.json();
        } else {
            const text = await response.text();
            console.error('\''[apiCall] Non-JSON response:'\'', text);
            return {
                ok: false,
                status: response.status,
                error: `Server returned non-JSON response: ${text.substring(0, 100)}`
            };
        }
        
        console.log('\''[apiCall] Response data:'\'', data);
        
        return {
            ok: response.ok,
            status: response.status,
            data
        };
    } catch (error) {
        console.error('\''[apiCall] Error:'\'', error);
        return {
            ok: false,
            status: 0,
            error: error.message
        };
    }
}
EOFAUTH
'

echo "✅ auth.js fixed!"

# Now verify
echo ""
echo "Verifying fix..."
docker exec smartcursor cat /app/static/js/auth.js | head -20

echo ""
echo "✅ Done! Please refresh your browser (Ctrl+F5) and test login."

