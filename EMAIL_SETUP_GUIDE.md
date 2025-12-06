# Email Setup Guide for Password Reset

## 📧 Email Configuration

The password reset system supports sending emails via SMTP (Gmail, etc.) or SendGrid. By default, email sending is disabled for development.

## 🔧 Setup Instructions

### Option 1: Gmail SMTP (Recommended for Development)

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate an App Password**:
   - Go to Google Account → Security → 2-Step Verification → App passwords
   - Create an app password for "Mail"
   - Copy the generated password

3. **Set Environment Variables**:

Create a `.env` file in the project root or set environment variables:

```bash
# Enable email sending
EMAIL_ENABLED=true

# Email provider (smtp or sendgrid)
EMAIL_PROVIDER=smtp

# Gmail SMTP Settings
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password-here
SMTP_USE_TLS=true

# Email From Settings
FROM_EMAIL=your-email@gmail.com
FROM_NAME=SmartCursor

# Base URL for reset links
BASE_URL=http://localhost:5050
```

### Option 2: Other SMTP Providers

For other email providers (Outlook, Yahoo, etc.), adjust the SMTP settings:

```bash
EMAIL_ENABLED=true
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.live.com  # Outlook
SMTP_PORT=587
SMTP_USER=your-email@outlook.com
SMTP_PASSWORD=your-password
SMTP_USE_TLS=true
FROM_EMAIL=your-email@outlook.com
FROM_NAME=SmartCursor
BASE_URL=http://localhost:5050
```

### Option 3: SendGrid (Production)

1. **Sign up for SendGrid** (free tier available)
2. **Create API Key**:
   - Go to SendGrid Dashboard → Settings → API Keys
   - Create API Key with "Mail Send" permissions
   - Copy the API key

3. **Set Environment Variables**:

```bash
EMAIL_ENABLED=true
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=your-api-key-here
FROM_EMAIL=your-verified-email@example.com
FROM_NAME=SmartCursor
BASE_URL=https://your-domain.com
```

4. **Install SendGrid Library**:
```bash
pip install sendgrid
```

## 🚀 Usage

### Development Mode (No Email)

By default, email sending is disabled. The reset token will be:
- Logged to console
- Shown in the response (for testing)

### Production Mode (With Email)

1. Set `EMAIL_ENABLED=true`
2. Configure your email provider settings
3. Reset tokens will be sent via email
4. Tokens won't be shown in responses

## 📝 Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `EMAIL_ENABLED` | Enable/disable email sending | `false` | No |
| `EMAIL_PROVIDER` | Email provider (`smtp` or `sendgrid`) | `smtp` | No |
| `SMTP_HOST` | SMTP server hostname | `smtp.gmail.com` | Yes (SMTP) |
| `SMTP_PORT` | SMTP server port | `587` | No |
| `SMTP_USER` | SMTP username (email) | - | Yes (SMTP) |
| `SMTP_PASSWORD` | SMTP password/app password | - | Yes (SMTP) |
| `SMTP_USE_TLS` | Use TLS encryption | `true` | No |
| `SENDGRID_API_KEY` | SendGrid API key | - | Yes (SendGrid) |
| `FROM_EMAIL` | Sender email address | SMTP_USER | No |
| `FROM_NAME` | Sender name | `SmartCursor` | No |
| `BASE_URL` | Base URL for reset links | `http://localhost:5050` | No |

## 🔒 Security Notes

1. **Never commit credentials** to version control
2. Use environment variables or `.env` file (add to `.gitignore`)
3. For production, use a dedicated email service (SendGrid, AWS SES, etc.)
4. Use app passwords for Gmail (not your regular password)
5. Enable 2FA on your email account

## 🧪 Testing

### Test Email Configuration

You can test email sending by:
1. Setting up environment variables
2. Requesting a password reset
3. Checking your email inbox
4. Checking server logs for email status

### Development Testing

Without email configured:
- Token is logged to console
- Token is shown in API response
- You can manually copy the reset link

## 📧 Email Template

The password reset email includes:
- Professional HTML template with branding
- Plain text fallback
- Reset link button
- Token expiration notice
- Security notice

## 🐛 Troubleshooting

### Email Not Sending

1. **Check environment variables** are set correctly
2. **Check server logs** for error messages
3. **Verify SMTP credentials** are correct
4. **Check firewall** isn't blocking SMTP port
5. **Test SMTP connection** separately

### Gmail Issues

- Make sure you're using an **App Password** (not regular password)
- Enable **"Less secure app access"** (if app passwords not available)
- Check Gmail isn't blocking the login attempt

### SendGrid Issues

- Verify API key is correct
- Check API key has "Mail Send" permissions
- Verify sender email is verified in SendGrid

## 📚 Additional Resources

- [Gmail App Passwords](https://support.google.com/accounts/answer/185833)
- [SendGrid Documentation](https://docs.sendgrid.com/)
- [Python SMTP Documentation](https://docs.python.org/3/library/smtplib.html)

