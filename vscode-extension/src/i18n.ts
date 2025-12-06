/**
 * Internationalization (i18n) module for VS Code extension.
 * Handles language selection and translations.
 */
import * as vscode from 'vscode';

export type Language = 'en' | 'zh';

const translations: Record<Language, Record<string, string>> = {
    en: {
        'welcome': 'Welcome',
        'loggedIn': 'Logged in as',
        'loginSuccess': 'Login successful',
        'signupSuccess': 'Account created successfully',
        'logoutSuccess': 'Logged out successfully',
        'selectLanguage': 'Select your preferred language',
        'languageSet': 'Language preference saved',
        'english': 'English',
        'chinese': '简体中文 (Simplified Chinese)'
    },
    zh: {
        'welcome': '欢迎',
        'loggedIn': '已登录为',
        'loginSuccess': '登录成功',
        'signupSuccess': '账户创建成功',
        'logoutSuccess': '登出成功',
        'selectLanguage': '选择您的首选语言',
        'languageSet': '语言偏好已保存',
        'english': 'English',
        'chinese': '简体中文'
    }
};

/**
 * Get current language preference from extension context.
 */
export async function getLanguage(context: vscode.ExtensionContext): Promise<Language> {
    const language = context.globalState.get<Language>('preferredLanguage');
    return language || 'en'; // Default to English
}

/**
 * Set language preference.
 */
export async function setLanguage(context: vscode.ExtensionContext, language: Language): Promise<void> {
    await context.globalState.update('preferredLanguage', language);
}

/**
 * Translate a key to the current language.
 */
export async function t(context: vscode.ExtensionContext, key: string): Promise<string> {
    const language = await getLanguage(context);
    return translations[language][key] || translations.en[key] || key;
}

/**
 * Prompt user to select language.
 * Returns the selected language or undefined if cancelled.
 */
export async function selectLanguage(context: vscode.ExtensionContext): Promise<Language | undefined> {
    const currentLang = await getLanguage(context);
    const currentLangText = currentLang === 'en' ? 'English' : '简体中文';
    
    const selected = await vscode.window.showQuickPick([
        {
            label: '$(globe) English',
            description: currentLang === 'en' ? '(Current)' : '',
            detail: 'Use English interface',
            value: 'en' as Language
        },
        {
            label: '$(globe) 简体中文',
            description: currentLang === 'zh' ? '(当前)' : '',
            detail: '使用简体中文界面',
            value: 'zh' as Language
        }
    ], {
        placeHolder: await t(context, 'selectLanguage'),
        ignoreFocusOut: false
    });

    if (selected) {
        await setLanguage(context, selected.value);
        const message = await t(context, 'languageSet');
        vscode.window.showInformationMessage(
            `${message}: ${selected.value === 'en' ? 'English' : '简体中文'}`
        );
        return selected.value;
    }

    return undefined;
}

/**
 * Show language selection prompt after login/signup.
 */
export async function promptLanguageSelection(context: vscode.ExtensionContext): Promise<void> {
    // Check if user has already set language preference
    const hasLanguagePreference = context.globalState.get<Language>('preferredLanguage') !== undefined;
    
    if (hasLanguagePreference) {
        // User already has a preference, don't force them to select again
        // But we can optionally show a message
        return;
    }

    // Show language selection prompt
    const action = await vscode.window.showInformationMessage(
        'Welcome! Please select your preferred language / 欢迎！请选择您的首选语言',
        'English',
        '简体中文'
    );

    if (action === 'English') {
        await setLanguage(context, 'en');
        vscode.window.showInformationMessage('Language set to English');
    } else if (action === '简体中文') {
        await setLanguage(context, 'zh');
        vscode.window.showInformationMessage('语言已设置为简体中文');
    }
}

