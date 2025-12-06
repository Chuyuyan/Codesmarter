/**
 * Account Page JavaScript
 * Handles account management, profile updates, password changes, etc.
 */

// Check authentication on page load
document.addEventListener('DOMContentLoaded', () => {
    checkAuthAndLoadProfile();
    setupNavigation();
    setupForms();
    setupPasswordToggles();
});

function checkAuthAndLoadProfile() {
    if (typeof TokenManager === 'undefined' || !TokenManager.isAuthenticated()) {
        window.location.href = '/login';
        return;
    }

    loadUserProfile();
}

async function loadUserProfile() {
    try {
        const result = await apiCall('/auth/me');
        
        if (result.ok && result.data.ok) {
            const user = result.data.user;
            displayUserProfile(user);
        } else {
            showAccountMessage('Failed to load profile. Please login again.', 'error');
            setTimeout(() => {
                window.location.href = '/login';
            }, 2000);
        }
    } catch (error) {
        console.error('[account] Error loading profile:', error);
        showAccountMessage('Network error. Please check if the server is running.', 'error');
    }
}

function displayUserProfile(user) {
    // Update profile display
    document.getElementById('profileUsername').textContent = user.username || '-';
    document.getElementById('profileEmail').textContent = user.email || '-';
    document.getElementById('profilePhone').textContent = user.phone_number || 'Not set';
    
    // Format date
    if (user.created_at) {
        const date = new Date(user.created_at);
        document.getElementById('profileCreatedAt').textContent = date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }

    // Set avatar initials
    const initials = (user.username || 'U').charAt(0).toUpperCase();
    document.getElementById('avatarInitials').textContent = initials;

    // Pre-fill update form
    document.getElementById('updateUsername').value = user.username || '';
    document.getElementById('updateEmail').value = user.email || '';
    const phoneInput = document.getElementById('updatePhone');
    if (phoneInput) {
        phoneInput.value = user.phone_number || '';
    }
}

// Navigation
function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            // Remove active class from all items
            navItems.forEach(nav => nav.classList.remove('active'));
            // Add active class to clicked item
            item.classList.add('active');

            // Show corresponding section
            const section = item.getAttribute('data-section');
            showSection(section);
        });
    });

    // Logout buttons (header and danger zone)
    const logoutBtn = document.getElementById('logoutBtn');
    const logoutBtnHeader = document.getElementById('logoutBtnHeader');
    
    function handleLogout() {
        if (typeof TokenManager !== 'undefined') {
            TokenManager.removeToken();
        }
        window.location.href = '/login';
    }
    
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }
    
    if (logoutBtnHeader) {
        logoutBtnHeader.addEventListener('click', handleLogout);
    }
}

function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });

    // Show selected section
    const section = document.getElementById(`${sectionName}-section`);
    if (section) {
        section.classList.add('active');
    }
}

// Forms
function setupForms() {
    // Update profile form
    const updateProfileForm = document.getElementById('updateProfileForm');
    if (updateProfileForm) {
        updateProfileForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            clearError('updateUsernameError');
            clearError('updateEmailError');
            clearError('updatePhoneError');

            const username = document.getElementById('updateUsername').value.trim();
            const email = document.getElementById('updateEmail').value.trim();
            const phoneNumber = document.getElementById('updatePhone')?.value.trim() || '';

            // Validation
            if (username && !validateUsername(username)) {
                showError('updateUsernameError', 'Username must be at least 3 characters');
                return;
            }

            if (email && !validateEmail(email)) {
                showError('updateEmailError', 'Please enter a valid email address');
                return;
            }

            // Validate phone number format (E.164) if provided
            if (phoneNumber && !/^\+[1-9]\d{1,14}$/.test(phoneNumber)) {
                showError('updatePhoneError', 'Phone number must be in E.164 format (e.g., +1234567890)');
                return;
            }

            if (!username && !email && !phoneNumber) {
                showAccountMessage('Please enter at least one field to update', 'error');
                return;
            }

            setLoading(updateProfileForm, true);

            try {
                const updateData = {};
                if (username) updateData.username = username;
                if (email) updateData.email = email;
                // Allow setting or clearing phone number
                if (phoneNumber) {
                    updateData.phone_number = phoneNumber;
                } else if (document.getElementById('updatePhone')) {
                    // Allow clearing phone number by sending null
                    updateData.phone_number = null;
                }

                const result = await apiCall('/auth/me', {
                    method: 'PUT',
                    body: JSON.stringify(updateData)
                });

                if (result.ok && result.data.ok) {
                    showAccountMessage('Profile updated successfully!', 'success');
                    loadUserProfile(); // Reload profile
                } else {
                    const errorMsg = result.data?.error || 'Failed to update profile';
                    showAccountMessage(errorMsg, 'error');
                    
                    if (errorMsg.includes('username')) {
                        showError('updateUsernameError', errorMsg);
                    } else if (errorMsg.includes('email')) {
                        showError('updateEmailError', errorMsg);
                    }
                }
            } catch (error) {
                showAccountMessage('Network error. Please check if the server is running.', 'error');
            } finally {
                setLoading(updateProfileForm, false);
            }
        });
    }

    // Change password form
    const changePasswordForm = document.getElementById('changePasswordForm');
    if (changePasswordForm) {
        changePasswordForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            clearError('currentPasswordError');
            clearError('newPasswordError');
            clearError('confirmNewPasswordError');

            const currentPassword = document.getElementById('currentPassword').value;
            const newPassword = document.getElementById('newPassword').value;
            const confirmPassword = document.getElementById('confirmNewPassword').value;

            // Validation
            let hasErrors = false;

            if (!currentPassword) {
                showError('currentPasswordError', 'Current password is required');
                hasErrors = true;
            }

            if (!validatePassword(newPassword)) {
                showError('newPasswordError', 'Password must be at least 6 characters');
                hasErrors = true;
            }

            if (newPassword !== confirmPassword) {
                showError('confirmNewPasswordError', 'Passwords do not match');
                hasErrors = true;
            }

            if (hasErrors) {
                return;
            }

            setLoading(changePasswordForm, true);

            try {
                // First, verify current password by trying to login
                const verifyResult = await apiCall('/auth/login', {
                    method: 'POST',
                    body: JSON.stringify({
                        username_or_email: document.getElementById('profileEmail').textContent,
                        password: currentPassword
                    })
                });

                if (!verifyResult.ok || !verifyResult.data.ok) {
                    showError('currentPasswordError', 'Current password is incorrect');
                    setLoading(changePasswordForm, false);
                    return;
                }

                // Update password
                const result = await apiCall('/auth/me', {
                    method: 'PUT',
                    body: JSON.stringify({
                        password: newPassword
                    })
                });

                if (result.ok && result.data.ok) {
                    showAccountMessage('Password changed successfully!', 'success');
                    changePasswordForm.reset();
                } else {
                    const errorMsg = result.data?.error || 'Failed to change password';
                    showAccountMessage(errorMsg, 'error');
                }
            } catch (error) {
                showAccountMessage('Network error. Please check if the server is running.', 'error');
            } finally {
                setLoading(changePasswordForm, false);
            }
        });
    }

    // Delete account
    const deleteAccountBtn = document.getElementById('deleteAccountBtn');
    const deleteModal = document.getElementById('deleteModal');
    const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');

    if (deleteAccountBtn) {
        deleteAccountBtn.addEventListener('click', () => {
            deleteModal.style.display = 'flex';
        });
    }

    if (cancelDeleteBtn) {
        cancelDeleteBtn.addEventListener('click', () => {
            deleteModal.style.display = 'none';
        });
    }

    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', async () => {
            try {
                const result = await apiCall('/auth/me', {
                    method: 'DELETE'
                });

                if (result.ok && result.data.ok) {
                    showAccountMessage('Account deleted successfully. Redirecting...', 'success');
                    TokenManager.removeToken();
                    setTimeout(() => {
                        window.location.href = '/register';
                    }, 2000);
                } else {
                    const errorMsg = result.data?.error || 'Failed to delete account';
                    showAccountMessage(errorMsg, 'error');
                    deleteModal.style.display = 'none';
                }
            } catch (error) {
                showAccountMessage('Network error. Please check if the server is running.', 'error');
                deleteModal.style.display = 'none';
            }
        });
    }

    // Close modal on outside click
    if (deleteModal) {
        deleteModal.addEventListener('click', (e) => {
            if (e.target === deleteModal) {
                deleteModal.style.display = 'none';
            }
        });
    }
}

// Password toggles
function setupPasswordToggles() {
    const toggles = document.querySelectorAll('#security-section .toggle-password');
    toggles.forEach(toggle => {
        // Remove all children first
        while (toggle.firstChild) {
            toggle.removeChild(toggle.firstChild);
        }
        
        // Create icon
        const eyeIcon = document.createElement('span');
        eyeIcon.className = 'eye-icon';
        eyeIcon.setAttribute('aria-hidden', 'true');
        toggle.appendChild(eyeIcon);
        
        // Get input
        const input = toggle.parentElement.querySelector('input');
        if (input) {
            if (input.type === 'password') {
                eyeIcon.textContent = '🙈';
            } else {
                eyeIcon.textContent = '👁';
            }
        }
        
        toggle.addEventListener('click', () => {
            const input = toggle.parentElement.querySelector('input');
            const icon = toggle.querySelector('.eye-icon');
            
            if (!input || !icon) return;
            
            if (input.type === 'password') {
                input.type = 'text';
                icon.textContent = '👁';
            } else {
                input.type = 'password';
                icon.textContent = '🙈';
            }
        });
    });
}

// Helper functions
function showAccountMessage(message, type = 'success') {
    const messageEl = document.getElementById('accountMessage');
    if (messageEl) {
        messageEl.textContent = message;
        messageEl.className = `auth-message ${type}`;
        messageEl.style.display = 'block';
        
        // Scroll to message
        messageEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            messageEl.style.display = 'none';
        }, 5000);
    }
}

function setLoading(form, loading) {
    const submitBtn = form.querySelector('button[type="submit"]');
    if (!submitBtn) return;
    
    const btnText = submitBtn.querySelector('.btn-text');
    const btnLoader = submitBtn.querySelector('.btn-loader');
    
    if (loading) {
        submitBtn.disabled = true;
        if (btnText) btnText.style.display = 'none';
        if (btnLoader) btnLoader.style.display = 'inline-block';
        form.classList.add('loading');
    } else {
        submitBtn.disabled = false;
        if (btnText) btnText.style.display = 'inline';
        if (btnLoader) btnLoader.style.display = 'none';
        form.classList.remove('loading');
    }
}

