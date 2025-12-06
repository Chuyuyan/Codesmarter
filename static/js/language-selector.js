/**
 * Language Selector Component
 */

function createLanguageSelector() {
    const selector = document.createElement('div');
    selector.className = 'language-selector';
    
    const btn = document.createElement('button');
    btn.className = 'language-btn';
    btn.innerHTML = '<span class="language-flag">🌐</span> <span id="currentLangText">Language</span>';
    
    const dropdown = document.createElement('div');
    dropdown.className = 'language-dropdown';
    
    const enOption = document.createElement('div');
    enOption.className = 'language-option';
    enOption.setAttribute('data-lang', 'en');
    enOption.innerHTML = '<span class="language-flag">🇺🇸</span> <span>English</span>';
    
    const zhOption = document.createElement('div');
    zhOption.className = 'language-option';
    zhOption.setAttribute('data-lang', 'zh');
    zhOption.innerHTML = '<span class="language-flag">🇨🇳</span> <span>简体中文</span>';
    
    dropdown.appendChild(enOption);
    dropdown.appendChild(zhOption);
    
    selector.appendChild(btn);
    selector.appendChild(dropdown);
    
    // Update active state
    function updateActive() {
        if (typeof i18n === 'undefined') return;
        const currentLang = i18n.getCurrentLanguage();
        enOption.classList.toggle('active', currentLang === 'en');
        zhOption.classList.toggle('active', currentLang === 'zh');
        const langText = document.getElementById('currentLangText');
        if (langText) {
            langText.textContent = currentLang === 'en' ? 'English' : '简体中文';
        }
    }
    
    // Toggle dropdown
    btn.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.classList.toggle('show');
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!selector.contains(e.target)) {
            dropdown.classList.remove('show');
        }
    });
    
    // Language selection
    enOption.addEventListener('click', () => {
        if (typeof i18n !== 'undefined') {
            i18n.setLanguage('en');
            updateActive();
        }
        dropdown.classList.remove('show');
    });
    
    zhOption.addEventListener('click', () => {
        if (typeof i18n !== 'undefined') {
            i18n.setLanguage('zh');
            updateActive();
        }
        dropdown.classList.remove('show');
    });
    
    // Update on language change
    window.addEventListener('languageChanged', updateActive);
    
    // Initial update (with delay to ensure i18n is ready)
    setTimeout(updateActive, 100);
    
    return selector;
}

// Auto-add language selector to common locations
function addLanguageSelectors() {
    // Wait for i18n to be available
    if (typeof i18n === 'undefined') {
        setTimeout(addLanguageSelectors, 100);
        return;
    }
    
    // Priority 1: Add to navbar placeholder (top navigation) - always visible
    const navbarPlaceholder = document.getElementById('languageSelectorPlaceholder');
    if (navbarPlaceholder) {
        // Only add if not already present
        if (!navbarPlaceholder.querySelector('.language-selector')) {
            const selector = createLanguageSelector();
            navbarPlaceholder.appendChild(selector);
            console.log('[language-selector] ✅ Added to navbar');
        } else {
            console.log('[language-selector] Already exists in navbar');
        }
        return; // Success, don't add to other locations
    } else {
        console.warn('[language-selector] ⚠️ languageSelectorPlaceholder not found!');
    }
    
    // Fallback: Add to auth status bar (home page) - if it exists
    const authStatusActions = document.querySelector('.auth-status-actions');
    if (authStatusActions && !authStatusActions.querySelector('.language-selector')) {
        const selector = createLanguageSelector();
        authStatusActions.insertBefore(selector, authStatusActions.firstChild);
        console.log('[language-selector] Added to auth status bar');
    }
    
    // Fallback: Add to main container header (home page)
    const mainHeader = document.querySelector('.container header');
    if (mainHeader && !mainHeader.querySelector('.language-selector')) {
        const selector = createLanguageSelector();
        mainHeader.style.position = 'relative';
        const selectorWrapper = document.createElement('div');
        selectorWrapper.style.position = 'absolute';
        selectorWrapper.style.top = '20px';
        selectorWrapper.style.right = '20px';
        selectorWrapper.appendChild(selector);
        mainHeader.appendChild(selectorWrapper);
        console.log('[language-selector] Added to main header');
    }
    
    // Add to account header
    const accountNav = document.querySelector('.account-nav');
    if (accountNav && !accountNav.querySelector('.language-selector')) {
        const selector = createLanguageSelector();
        accountNav.insertBefore(selector, accountNav.firstChild);
        console.log('[language-selector] Added to account nav');
    }
    
    // Add to auth pages header
    const authHeader = document.querySelector('.auth-header');
    if (authHeader && !authHeader.querySelector('.language-selector')) {
        authHeader.style.position = 'relative';
        const selector = createLanguageSelector();
        authHeader.appendChild(selector);
        console.log('[language-selector] Added to auth header');
    }
}

// Run on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(addLanguageSelectors, 200);
    });
} else {
    setTimeout(addLanguageSelectors, 200);
}

// Also try after a delay in case elements are added dynamically
setTimeout(addLanguageSelectors, 1000);
setTimeout(addLanguageSelectors, 2000);

