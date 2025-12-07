/**
 * Landing Page JavaScript
 * Handles landing page interactions and redirects
 */

document.addEventListener('DOMContentLoaded', () => {
    // Check if user is already logged in
    if (window.TokenManager && window.TokenManager.isAuthenticated()) {
        // Verify token is still valid
        if (window.apiCall) {
            window.apiCall('/auth/me').then(result => {
                if (result.ok && result.data && result.data.ok) {
                    // User is logged in, redirect to dashboard
                    window.location.href = '/dashboard';
                } else {
                    // Token invalid, clear it
                    window.TokenManager.removeToken();
                }
            });
        }
    }
    
    // Add smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});

