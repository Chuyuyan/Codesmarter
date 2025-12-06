# Authentication Testing Guide

## 🧪 Test Scripts

### Backend API Tests
**File:** `test_auth_api.py`

Tests all authentication endpoints:
- ✅ Server health check
- ✅ User registration
- ✅ Duplicate registration rejection
- ✅ User login
- ✅ Invalid login rejection
- ✅ Get current user (with token)
- ✅ Get current user (without token - should fail)
- ✅ Update user profile
- ✅ Logout handling

### Running Backend Tests

1. **Start the backend server:**
   ```bash
   # Option 1: Direct Python
   python -m backend.app
   
   # Option 2: PowerShell script
   .\start_server.ps1
   
   # Option 3: Batch script
   .\start_server.bat
   ```

2. **Run the test:**
   ```bash
   python test_auth_api.py
   ```

3. **Expected output:**
   ```
   ============================================================
   Authentication API Test Suite
   ============================================================
   
   === Testing Server Health ===
   [OK] Server is running
   
   === Testing User Registration ===
   [OK] User registered successfully
   
   === Testing User Login ===
   [OK] Login successful
   
   ... (more tests)
   
   ============================================================
   Test Summary
   ============================================================
   [OK] Registration
   [OK] Login
   [OK] Get Current User
   ...
   
   Total: 8/8 tests passed
   [SUCCESS] All tests passed! ✅
   ```

## 🔌 VS Code Extension Tests

### Manual Testing Steps

1. **Open VS Code with the extension loaded**

2. **Test Signup:**
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
   - Type: `Code Assistant: Sign Up`
   - Enter:
     - Username: `testuser123`
     - Email: `test@example.com`
     - Password: `testpass123`
     - Confirm Password: `testpass123`
   - ✅ Should see: "Account created and logged in as testuser123"
   - ✅ Status bar should show: `👤 testuser123`

3. **Test Login:**
   - Press `Ctrl+Shift+P`
   - Type: `Code Assistant: Logout`
   - Press `Ctrl+Shift+P`
   - Type: `Code Assistant: Login`
   - Enter:
     - Username/Email: `testuser123`
     - Password: `testpass123`
   - ✅ Should see: "Logged in as testuser123"
   - ✅ Status bar should update

4. **Test Profile:**
   - Click on status bar (shows username)
   - Or use command: `Code Assistant: Show Profile`
   - ✅ Should see user info

5. **Test Logout:**
   - Press `Ctrl+Shift+P`
   - Type: `Code Assistant: Logout`
   - ✅ Should see: "Logged out successfully"
   - ✅ Status bar should show: `🔐 Login`

6. **Test Invalid Login:**
   - Try logging in with wrong password
   - ✅ Should see error message

## 🐛 Troubleshooting

### Server Not Running
**Error:** `Cannot connect to server`

**Solution:**
1. Check if server is running on port 5050
2. Start server: `python -m backend.app`
3. Check server logs for errors

### Database Errors
**Error:** `Registration failed: ...`

**Solution:**
1. Check if database file exists: `data/users.db`
2. Check file permissions
3. Delete database file to reset: `rm data/users.db` (will lose all users)

### Extension Not Working
**Error:** Commands not appearing

**Solution:**
1. Reload VS Code window: `Ctrl+Shift+P` → `Developer: Reload Window`
2. Check extension is activated (check Output panel)
3. Rebuild extension: `npm run compile` in `vscode-extension/`

### Token Issues
**Error:** `Invalid or expired token`

**Solution:**
1. Logout and login again
2. Check token expiration (default: 7 days)
3. Verify server JWT_SECRET_KEY is consistent

## 📊 Test Coverage

### Backend API Endpoints
- [x] `POST /auth/register` - Registration
- [x] `POST /auth/login` - Login
- [x] `GET /auth/me` - Get current user (with token)
- [x] `GET /auth/me` - Get current user (without token - should fail)
- [x] `PUT /auth/me` - Update user profile
- [x] `DELETE /auth/me` - Delete user account

### VS Code Extension
- [x] Signup command
- [x] Login command
- [x] Logout command
- [x] Profile command
- [x] Status bar integration
- [x] Token storage
- [x] Token verification

## 🎯 Quick Test Checklist

### Backend
- [ ] Server starts without errors
- [ ] Database file created: `data/users.db`
- [ ] Registration endpoint works
- [ ] Login endpoint works
- [ ] Protected endpoints require token
- [ ] Token verification works

### Extension
- [ ] Extension loads without errors
- [ ] Status bar shows login state
- [ ] Signup command works
- [ ] Login command works
- [ ] Logout command works
- [ ] Profile command works
- [ ] Token stored securely
- [ ] Token persists after VS Code restart

## 📝 Notes

- **Test Users:** Each test run creates a new test user with random username
- **Database:** SQLite database at `data/users.db`
- **Tokens:** JWT tokens expire after 7 days (configurable)
- **Security:** Passwords are hashed using Werkzeug (never stored in plain text)

## 🔄 Continuous Testing

For automated testing, you can:
1. Start server in background
2. Run `test_auth_api.py`
3. Check exit code (0 = success, 1 = failure)
4. Stop server

Example script:
```bash
# Start server
python -m backend.app &
SERVER_PID=$!

# Wait for server to start
sleep 3

# Run tests
python test_auth_api.py
TEST_RESULT=$?

# Stop server
kill $SERVER_PID

# Exit with test result
exit $TEST_RESULT
```

