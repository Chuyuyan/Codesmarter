# Environment Variables Configuration

## 📝 Adding SMS Configuration to .env

You already have a `.env` file! Just add these lines to it:

```bash
# SMS Configuration (Twilio)
SMS_ENABLED=true
TWILIO_ACCOUNT_SID=ACXXXXXXXXXXXXXXXXXXXXXXXXXXXX
TWILIO_AUTH_TOKEN=YOUR_TWILIO_AUTH_TOKEN_HERE
TWILIO_FROM_NUMBER=+1234567890

# Base URL for reset links
BASE_URL=http://localhost:5050
```

## ✅ Format Rules

- **No quotes** around values
- **No spaces** around the `=` sign
- One variable per line
- Comments start with `#`

## 📍 Where to Add

Add these lines at the **end** of your existing `.env` file.

## 🔄 After Adding

1. **Save** the `.env` file
2. **Restart** your Flask server:
   ```bash
   python -m backend.app
   ```
3. The server will automatically load the new environment variables

## 🔍 Verify It's Working

After restarting, check server logs when requesting password reset:
- If SMS is configured correctly: `[password_reset] Password reset SMS sent to +1234567890`
- If not configured: `[password_reset] Reset token for email@example.com: ...` (dev mode)

## 🛡️ Security Note

Make sure your `.env` file is in `.gitignore` (it should be) so you don't commit your credentials!

