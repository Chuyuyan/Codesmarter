# SMS Setup Guide for Password Reset

## 📱 SMS Configuration

The password reset system now supports sending SMS via Twilio. Users can receive password reset links via SMS instead of (or in addition to) email.

## 🔧 Setup Instructions

### 1. Install Twilio Library

```bash
pip install twilio python-dotenv
```

### 2. Get Twilio Credentials

1. **Sign up for Twilio** (free trial available): https://www.twilio.com/
2. **Get Account SID and Auth Token** from Twilio Console
3. **Get a Twilio Phone Number** (or use Messaging Service SID)

### 3. Configure Environment Variables

Create a `.env` file in the project root or set environment variables:

```bash
# Enable SMS sending
SMS_ENABLED=true

# Twilio Configuration
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_FROM_NUMBER=+1234567890  # Your Twilio phone number (E.164 format)
# OR use messaging service:
TWILIO_MESSAGING_SERVICE_SID=your_messaging_service_sid

# Base URL for reset links
BASE_URL=http://localhost:5050

# Optional: Enable email too (for dual notification)
EMAIL_ENABLED=true
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### 4. Add Phone Number to User Account

Users need to add their phone number to their account. This can be done:

- **During registration** (add phone field to register form)
- **In account settings** (add phone field to account page)
- **Via API** (update user profile)

## 📱 Phone Number Format

Phone numbers must be in **E.164 format**:
- US: `+1234567890`
- International: `+1234567890` (country code + number)
- Must include country code and start with `+`

## 🚀 Usage

### Option 1: SMS Only

Set `SMS_ENABLED=true` and configure Twilio. Users with phone numbers will receive SMS.

### Option 2: Email Only

Set `EMAIL_ENABLED=true` and configure email. Users will receive emails.

### Option 3: Both SMS + Email

Set both `SMS_ENABLED=true` and `EMAIL_ENABLED=true`. Users will receive both if they have both email and phone number.

## 🔒 Security Notes

1. **Never commit credentials** to version control
2. Use environment variables or `.env` file (add to `.gitignore`)
3. Store phone numbers securely in database
4. Validate phone number format before storing
5. Consider rate limiting for SMS to prevent abuse

## 📋 Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SMS_ENABLED` | Enable/disable SMS sending | `false` | No |
| `TWILIO_ACCOUNT_SID` | Twilio Account SID | - | Yes (SMS) |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token | - | Yes (SMS) |
| `TWILIO_FROM_NUMBER` | Twilio phone number | - | Yes* (SMS) |
| `TWILIO_MESSAGING_SERVICE_SID` | Twilio Messaging Service SID | - | No |
| `BASE_URL` | Base URL for reset links | `http://localhost:5050` | No |

*Either `TWILIO_FROM_NUMBER` or `TWILIO_MESSAGING_SERVICE_SID` is required.

## 🧪 Testing

### Test SMS Sending

1. Set up environment variables
2. Add phone number to user account
3. Request password reset
4. Check SMS inbox
5. Check server logs for SMS status

### Development Mode

Without SMS configured:
- Token is logged to console
- Token is shown in API response
- You can manually copy the reset link

## 📧 SMS Message Format

The password reset SMS includes:
- Greeting with username (if available)
- Reset link
- Expiration notice (1 hour)
- Security notice

## 🐛 Troubleshooting

### SMS Not Sending

1. **Check environment variables** are set correctly
2. **Check server logs** for error messages
3. **Verify Twilio credentials** are correct
4. **Check phone number format** (must be E.164)
5. **Verify Twilio account** has sufficient credits
6. **Check Twilio console** for delivery status

### Twilio Errors

- **"Invalid phone number"**: Check E.164 format
- **"Authentication failed"**: Check Account SID and Auth Token
- **"From number not valid"**: Verify Twilio phone number
- **"Insufficient balance"**: Add credits to Twilio account

## 📚 Additional Resources

- [Twilio Documentation](https://www.twilio.com/docs)
- [E.164 Phone Number Format](https://www.twilio.com/docs/glossary/what-e164)
- [Twilio Python SDK](https://www.twilio.com/docs/libraries/python)

## 💡 Notes

- SMS is more expensive than email (Twilio charges per message)
- Consider SMS for 2FA or urgent notifications
- Email is more standard for password reset
- Can use both for redundancy

