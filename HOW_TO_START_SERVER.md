# 🚀 How to Start the Server - Complete Tutorial

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Method 1: Using PowerShell Script (Easiest)](#method-1-using-powershell-script-easiest)
3. [Method 2: Using Batch Script](#method-2-using-batch-script)
4. [Method 3: Manual Start (Step-by-Step)](#method-3-manual-start-step-by-step)
5. [Troubleshooting](#troubleshooting)
6. [Verifying the Server is Running](#verifying-the-server-is-running)
7. [Stopping the Server](#stopping-the-server)

---

## ✅ Prerequisites

Before starting the server, make sure you have:

1. **Python installed** (3.8 or higher)
   - Check: `python --version`
   
2. **Dependencies installed**
   - Check: `pip list` should show `flask`, `faiss-cpu`, etc.
   - If not: `pip install -r requirements.txt`

3. **Virtual environment** (optional but recommended)
   - Check: Look for `.venv` folder in project root
   - If not: `python -m venv .venv`

4. **Environment variables** (optional)
   - Check: Look for `.env` file
   - If not: Create one with your API keys (see below)

---

## 🎯 Method 1: Using PowerShell Script (Easiest)

### **Step 1: Open PowerShell**
- Press `Win + X`
- Select "Windows PowerShell" or "Terminal"
- Or search "PowerShell" in Start menu

### **Step 2: Navigate to Project Directory**
```powershell
cd C:\Users\57811\smartcursor
```

### **Step 3: Run the Script**
```powershell
.\start_server.ps1
```

### **What Happens:**
1. Script activates virtual environment (if exists)
2. Starts Flask server
3. Shows: `Running on http://0.0.0.0:5050`

### **✅ Success!**
You should see:
```
Starting Flask server...
Open your browser at: http://127.0.0.1:5050
Press Ctrl+C to stop the server

 * Serving Flask app 'backend.app'
 * Debug mode: on
WARNING: This is a development server...
 * Running on http://0.0.0.0:5050
Press CTRL+C to quit
```

**Keep this window open!** The server runs in this terminal.

---

## 🎯 Method 2: Using Batch Script

### **Step 1: Open Command Prompt**
- Press `Win + R`
- Type `cmd` and press Enter
- Or search "Command Prompt" in Start menu

### **Step 2: Navigate to Project Directory**
```cmd
cd C:\Users\57811\smartcursor
```

### **Step 3: Run the Script**
```cmd
start_server.bat
```

### **What Happens:**
- Same as PowerShell script, but for Command Prompt

---

## 🎯 Method 3: Manual Start (Step-by-Step)

### **Step 1: Open Terminal**
- PowerShell, Command Prompt, or VS Code Terminal
- Navigate to project: `cd C:\Users\57811\smartcursor`

### **Step 2: Activate Virtual Environment (if using)**
```powershell
# PowerShell
.\.venv\Scripts\Activate.ps1

# Command Prompt
.venv\Scripts\activate.bat
```

**You should see:**
```
(.venv) PS C:\Users\57811\smartcursor>
```
The `(.venv)` prefix means virtual environment is active.

### **Step 3: Start the Server**
```powershell
python -m backend.app
```

### **Step 4: Wait for Server to Start**
You should see:
```
[privacy] Privacy mode DISABLED - Using disk storage
 * Serving Flask app 'backend.app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment.
 * Running on http://0.0.0.0:5050
Press CTRL+C to quit
```

**✅ Server is now running!**

---

## 🔍 Verifying the Server is Running

### **Method 1: Check Terminal Output**
Look for: `Running on http://0.0.0.0:5050`

### **Method 2: Health Check (PowerShell)**
Open a **new** PowerShell window:
```powershell
Invoke-RestMethod -Uri http://127.0.0.1:5050/health
```

**Expected output:**
```json
{
  "ok": true,
  "port": 5050
}
```

### **Method 3: Browser Test**
1. Open your web browser
2. Go to: `http://127.0.0.1:5050/health`
3. Should see: `{"ok": true, "port": 5050}`

### **Method 4: Check Process**
```powershell
Get-Process python | Where-Object {$_.CommandLine -like "*backend.app*"}
```

---

## 🛑 Stopping the Server

### **Method 1: Keyboard Shortcut**
1. Click on the terminal window where server is running
2. Press `Ctrl + C`
3. Server stops

### **Method 2: Close Terminal**
- Close the terminal window
- Server stops automatically

---

## ⚠️ Troubleshooting

### **Problem 1: "python: command not found"**

**Solution:**
```powershell
# Check if Python is installed
python --version

# If not found, try:
py --version

# If py works, use py instead:
py -m backend.app
```

### **Problem 2: "ModuleNotFoundError: No module named 'flask'"**

**Solution:**
```powershell
# Install dependencies
pip install -r requirements.txt

# Or install Flask specifically
pip install flask
```

### **Problem 3: "Port 5050 is already in use"**

**Error message:**
```
OSError: [Errno 48] Address already in use
```

**Solution:**
1. Find what's using port 5050:
   ```powershell
   netstat -ano | findstr :5050
   ```
2. Kill the process (replace PID with actual number):
   ```powershell
   taskkill /PID <PID> /F
   ```
3. Or change port in `backend/app.py`:
   ```python
   app.run(host="0.0.0.0", port=5051, debug=True)  # Use 5051 instead
   ```

### **Problem 4: "Permission denied" (PowerShell script)**

**Solution:**
```powershell
# Allow script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then try again
.\start_server.ps1
```

### **Problem 5: "Cannot activate virtual environment"**

**Solution:**
```powershell
# Create virtual environment if it doesn't exist
python -m venv .venv

# Then activate it
.\.venv\Scripts\Activate.ps1
```

### **Problem 6: Server starts but requests fail**

**Check:**
1. Is server actually running? (Check terminal output)
2. Are you using correct URL? (`http://127.0.0.1:5050`)
3. Check firewall settings
4. Try `http://localhost:5050` instead

---

## 📝 Quick Reference

### **Start Server:**
```powershell
# Easiest way
.\start_server.ps1

# Or manually
python -m backend.app
```

### **Check if Running:**
```powershell
Invoke-RestMethod -Uri http://127.0.0.1:5050/health
```

### **Stop Server:**
```
Press Ctrl + C in the terminal
```

### **Server URL:**
```
http://127.0.0.1:5050
or
http://localhost:5050
```

---

## 🎓 Understanding What's Happening

### **When You Start the Server:**

1. **Python loads** `backend/app.py`
2. **Flask application starts** listening on port 5050
3. **Server waits** for incoming requests
4. **VS Code extension** can now connect
5. **Test scripts** can now send requests
6. **API endpoints** become available

### **Server Status Indicators:**

| Status | What You See | Meaning |
|--------|-------------|---------|
| ✅ **Starting** | `Serving Flask app 'backend.app'` | Server is initializing |
| ✅ **Running** | `Running on http://0.0.0.0:5050` | Server is ready! |
| ⚠️ **Error** | `OSError: [Errno 48]` | Port already in use |
| ⚠️ **Error** | `ModuleNotFoundError` | Missing dependencies |

---

## 💡 Pro Tips

### **Tip 1: Keep Terminal Open**
- Server runs in the foreground
- Closing terminal stops the server
- Keep it open while using the system

### **Tip 2: Use VS Code Integrated Terminal**
- Open VS Code
- Press `` Ctrl + ` `` (backtick) to open terminal
- Run server from there
- See logs directly in VS Code

### **Tip 3: Run in Background (Advanced)**
```powershell
# PowerShell background job
Start-Job -ScriptBlock { python -m backend.app }

# Or use nohup (if available)
nohup python -m backend.app &
```

### **Tip 4: Auto-Start on Boot (Advanced)**
- Create Windows Task Scheduler task
- Or use Windows Service wrapper
- (Not recommended for development)

---

## ✅ Checklist: Is Everything Ready?

Before starting the server, check:

- [ ] Python is installed (`python --version`)
- [ ] Dependencies are installed (`pip list` shows `flask`)
- [ ] Virtual environment exists (optional)
- [ ] `.env` file exists with API keys (optional)
- [ ] Port 5050 is free
- [ ] You're in the project directory

---

## 🎯 Summary

**To start the server:**

1. **Open terminal** (PowerShell or Command Prompt)
2. **Navigate** to project: `cd C:\Users\57811\smartcursor`
3. **Run script**: `.\start_server.ps1`
   - OR manually: `python -m backend.app`
4. **Wait** for: `Running on http://0.0.0.0:5050`
5. **Keep terminal open** while using the system
6. **Press Ctrl+C** to stop

**That's it!** 🎉

The server is now running and ready to process requests from:
- VS Code extension
- Test scripts
- API calls
- Web browser

---

## 📚 Next Steps

After server is running:

1. **Test it**: `Invoke-RestMethod -Uri http://127.0.0.1:5050/health`
2. **Use VS Code extension**: It will connect automatically
3. **Run tests**: `python test_full_stack_generation.py`
4. **Index a repo**: `Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5050/index_repo -Body @{repo_path="C:\path\to\repo"} -ContentType "application/json"`

Happy coding! 🚀

