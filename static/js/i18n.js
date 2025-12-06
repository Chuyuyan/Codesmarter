/**
 * Internationalization (i18n) Support
 * Supports English and Mainland Chinese (Simplified)
 */

const i18n = {
    currentLang: 'en',
    translations: {
        en: {
            // Common
            'home': 'Home',
            'myAccount': 'My Account',
            'logout': 'Logout',
            'login': 'Login',
            'register': 'Register',
            'language': 'Language',
            'english': 'English',
            'chinese': '简体中文',
            
            // Home Page
            'codeAnalysisAssistant': 'Code Analysis Assistant',
            'analyzeYourCodebase': 'Analyze your codebase with AI - like Cursor',
            'indexRepository': 'Index Repository',
            'indexRepositoryDesc': 'Index your repository to enable code analysis. This creates a searchable index of your codebase.',
            'repositoryPath': 'Repository Path:',
            'indexRepositoryBtn': 'Index Repository',
            'askQuestions': 'Ask Questions About Your Code',
            'askQuestionsDesc': 'Ask questions about your codebase and get AI-powered answers with code citations.',
            'yourQuestion': 'Your Question:',
            'analysisType': 'Analysis Type:',
            'autoDetectMode': 'Auto-detect analysis type',
            'generate': 'Generate - Create or generate new code/project',
            'explain': 'Explain - Explain what the code does',
            'refactor': 'Refactor - Suggest refactoring improvements',
            'debug': 'Debug - Help identify bugs and issues',
            'optimize': 'Optimize - Suggest performance optimizations',
            'askQuestionBtn': 'Ask Question',
            'answer': 'Answer',
            'codeCitations': 'Code Citations',
            'loggedInAs': 'Logged in as',
            
            // Login Page
            'loginTitle': 'Login',
            'loginSubtitle': 'Sign in to your account',
            'usernameOrEmail': 'Username or Email',
            'password': 'Password',
            'forgotPassword': 'Forgot password?',
            'loginBtn': 'Sign In',
            'noAccount': "Don't have an account?",
            'signUp': 'Sign up',
            'rememberPassword': 'Remember your password?',
            'signIn': 'Sign in',
            
            // Register Page
            'registerTitle': 'Create Account',
            'registerSubtitle': 'Sign up to get started',
            'username': 'Username',
            'email': 'Email',
            'confirmPassword': 'Confirm Password',
            'registerBtn': 'Create Account',
            'haveAccount': 'Already have an account?',
            
            // Forgot Password
            'resetPassword': 'Reset Password',
            'resetPasswordDesc': 'Enter your email to receive a password reset link',
            'emailAddress': 'Email Address',
            'sendResetLink': 'Send Reset Link',
            
            // Account Page
            'profileInformation': 'Profile Information',
            'manageAccountProfile': 'Manage your account profile',
            'memberSince': 'Member Since',
            'accountStatus': 'Account Status',
            'active': 'Active',
            'updateProfile': 'Update Profile',
            'security': 'Security',
            'changePassword': 'Change Password',
            'currentPassword': 'Current Password',
            'newPassword': 'New Password',
            'confirmNewPassword': 'Confirm New Password',
            'updatePasswordBtn': 'Update Password',
            'settings': 'Settings',
            'dangerZone': 'Danger Zone',
            'deleteAccount': 'Delete Account',
            'deleteAccountDesc': 'Once you delete your account, there is no going back. Please be certain.',
            'deleteAccountBtn': 'Delete My Account',
            'activeSessions': 'Active Sessions',
            'loggedInOnDevice': 'You are currently logged in on this device',
            'phoneNumber': 'Phone Number',
            'notSet': 'Not set',
            'phoneNumberDesc': 'Optional: Add phone number to receive SMS password reset links',
            'phoneNumberFormat': 'Phone Number (E.164 format: +1234567890)',
            
            // Messages
            'loginSuccessful': 'Login successful! Redirecting...',
            'registrationSuccessful': 'Registration successful! Redirecting...',
            'profileUpdated': 'Profile updated successfully!',
            'passwordUpdated': 'Password updated successfully!',
            'accountDeleted': 'Account deleted successfully',
            'resetLinkSent': 'If an account with that email exists, a password reset link has been sent.',
            'developmentMode': 'Development Mode',
            'emailSmsNotConfigured': 'Email/SMS sending not configured. Token shown for development/testing.'
        },
        zh: {
            // Common
            'home': '首页',
            'myAccount': '我的账户',
            'logout': '退出登录',
            'login': '登录',
            'register': '注册',
            'language': '语言',
            'english': 'English',
            'chinese': '简体中文',
            
            // Home Page
            'codeAnalysisAssistant': '代码分析助手',
            'analyzeYourCodebase': '使用 AI 分析您的代码库 - 类似 Cursor',
            'indexRepository': '索引仓库',
            'indexRepositoryDesc': '索引您的仓库以启用代码分析。这将创建您代码库的可搜索索引。',
            'repositoryPath': '仓库路径:',
            'indexRepositoryBtn': '索引仓库',
            'askQuestions': '询问关于您的代码的问题',
            'askQuestionsDesc': '询问关于您代码库的问题，并获得带有代码引用的 AI 驱动答案。',
            'yourQuestion': '您的问题:',
            'analysisType': '分析类型:',
            'autoDetectMode': '自动检测分析类型',
            'generate': '生成 - 创建或生成新代码/项目',
            'explain': '解释 - 解释代码的作用',
            'refactor': '重构 - 建议重构改进',
            'debug': '调试 - 帮助识别错误和问题',
            'optimize': '优化 - 建议性能优化',
            'askQuestionBtn': '提问',
            'answer': '答案',
            'codeCitations': '代码引用',
            'loggedInAs': '已登录为',
            
            // Login Page
            'loginTitle': '登录',
            'loginSubtitle': '登录您的账户',
            'usernameOrEmail': '用户名或邮箱',
            'password': '密码',
            'forgotPassword': '忘记密码？',
            'loginBtn': '登录',
            'noAccount': '还没有账户？',
            'signUp': '注册',
            'rememberPassword': '记得密码？',
            'signIn': '登录',
            
            // Register Page
            'registerTitle': '创建账户',
            'registerSubtitle': '注册以开始使用',
            'username': '用户名',
            'email': '邮箱',
            'confirmPassword': '确认密码',
            'registerBtn': '创建账户',
            'haveAccount': '已有账户？',
            
            // Forgot Password
            'resetPassword': '重置密码',
            'resetPasswordDesc': '输入您的邮箱以接收密码重置链接',
            'emailAddress': '邮箱地址',
            'sendResetLink': '发送重置链接',
            
            // Account Page
            'profileInformation': '个人信息',
            'manageAccountProfile': '管理您的账户资料',
            'memberSince': '注册时间',
            'accountStatus': '账户状态',
            'active': '活跃',
            'updateProfile': '更新资料',
            'security': '安全',
            'changePassword': '修改密码',
            'currentPassword': '当前密码',
            'newPassword': '新密码',
            'confirmNewPassword': '确认新密码',
            'updatePasswordBtn': '更新密码',
            'settings': '设置',
            'dangerZone': '危险区域',
            'deleteAccount': '删除账户',
            'deleteAccountDesc': '一旦删除您的账户，将无法恢复。请确认。',
            'deleteAccountBtn': '删除我的账户',
            'activeSessions': '活动会话',
            'loggedInOnDevice': '您当前在此设备上登录',
            'phoneNumber': '电话号码',
            'notSet': '未设置',
            'phoneNumberDesc': '可选：添加电话号码以接收短信密码重置链接',
            'phoneNumberFormat': '电话号码 (E.164 格式: +1234567890)',
            
            // Messages
            'loginSuccessful': '登录成功！正在跳转...',
            'registrationSuccessful': '注册成功！正在跳转...',
            'profileUpdated': '资料更新成功！',
            'passwordUpdated': '密码更新成功！',
            'accountDeleted': '账户删除成功',
            'resetLinkSent': '如果该邮箱存在账户，密码重置链接已发送。',
            'developmentMode': '开发模式',
            'emailSmsNotConfigured': '未配置邮件/短信发送。显示令牌用于开发/测试。'
        }
    },
    
    /**
     * Initialize i18n system
     */
    init() {
        // Load saved language preference
        const savedLang = localStorage.getItem('preferredLanguage') || 'en';
        this.setLanguage(savedLang);
    },
    
    /**
     * Set language
     */
    setLanguage(lang) {
        if (!this.translations[lang]) {
            console.warn(`Language ${lang} not found, using English`);
            lang = 'en';
        }
        
        this.currentLang = lang;
        localStorage.setItem('preferredLanguage', lang);
        
        // Update all elements with data-i18n attribute
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = this.t(key);
            if (translation) {
                if (element.tagName === 'INPUT' && element.type === 'submit') {
                    element.value = translation;
                } else if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                    element.placeholder = translation;
                } else {
                    element.textContent = translation;
                }
            }
        });
        
        // Update title attributes
        document.querySelectorAll('[data-i18n-title]').forEach(element => {
            const key = element.getAttribute('data-i18n-title');
            element.title = this.t(key);
        });
        
        // Update placeholder attributes
        document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
            const key = element.getAttribute('data-i18n-placeholder');
            element.placeholder = this.t(key);
        });
        
        // Trigger custom event for components that need to update
        window.dispatchEvent(new CustomEvent('languageChanged', { detail: { lang } }));
    },
    
    /**
     * Translate a key
     */
    t(key) {
        return this.translations[this.currentLang][key] || this.translations['en'][key] || key;
    },
    
    /**
     * Get current language
     */
    getCurrentLanguage() {
        return this.currentLang;
    }
};

// Initialize on load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => i18n.init());
} else {
    i18n.init();
}

