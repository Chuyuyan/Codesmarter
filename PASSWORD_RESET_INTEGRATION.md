# Password Reset - SMS Integration

## ✅ SMS Module Created

I've created an SMS module based on your Twilio code and integrated it into password reset!

## 📁 Files Created/Updated

### New Files
- `backend/modules/sms_sender.py` - SMS sending module using Twilio
- `SMS_SETUP_GUIDE.md` - Complete SMS setup guide

### Updated Files
- `backend/modules/user_auth.py` - Added SMS support to password reset
- `requirements.txt` - Added `twilio` and `python-dotenv`

## 🔧 Setup Instructions

### 1. Install Dependencies

```bash
pip install twilio python-dotenv
```

### 2. Create `.env` File

Create a `.env` file in the project root with your Twilio credentials:

```bash
# Enable SMS sending
SMS_ENABLED=true

# Twilio Configuration
TWILIO_ACCOUNT_SID=ACXXXXXXXXXXXXXXXXXXXXXXXXXXXX
TWILIO_AUTH_TOKEN=YOUR_TWILIO_AUTH_TOKEN_HERE
TWILIO_FROM_NUMBER=+1234567890

# Base URL for reset links
BASE_URL=http://localhost:5050
```

### 3. Restart Server

Restart your Flask server to load the new environment variables.

## 📱 How It Works

### Current Flow

1. User requests password reset via email
2. System generates reset token
3. **If SMS enabled AND user has phone number:**
   - Sends SMS with reset link
4. **If email enabled:**
   - Sends email with reset link
5. **If neither configured:**
   - Shows token in console/response (dev mode)

### Options

**Option 1: SMS Only**
- Set `SMS_ENABLED=true`
- Add phone numbers to user accounts
- Users receive SMS with reset link

**Option 2: Email Only**
- Set `EMAIL_ENABLED=true`
- Users receive email with reset link

**Option 3: Both SMS + Email**
- Set both `SMS_ENABLED=true` and `EMAIL_ENABLED=true`
- Users receive both (if they have both email and phone)

## 🚀 Next Steps

### 1. Add Phone Number to User Model (Optional)

If you want users to add phone numbers:

- Add phone field to registration form
- Add phone field to account settings page
- Or update via API

### 2. Test SMS Sending

1. Set `SMS_ENABLED=true` in `.env`
2. Add phone number to a user account (via database or API)
3. Request password reset
4. Check SMS inbox

## 📝 Notes

- **Phone numbers** need to be in E.164 format: `+1234567890`
- **SMS is optional** - password reset works with or without it
- **Current behavior**: Shows token in console (dev mode) until SMS/email configured
- **Phone number field** added to User model (optional field)

## 🔒 Security

- Never commit `.env` file to git
- Keep Twilio credentials secure
- Validate phone numbers before storing

