# 🚀 Quick Start Guide - Run Code & Open Web UI

## ✅ Step-by-Step Instructions

### **Step 1: Open Terminal**

**PowerShell (Recommended):**
- Press `Win + X`
- Select "Windows PowerShell" or "Terminal"
- Or search "PowerShell" in Start menu

**OR Command Prompt:**
- Press `Win + R`
- Type `cmd` and press Enter

---

### **Step 2: Navigate to Project Directory**

```powershell
cd C:\Users\57811\smartcursor
```

---

### **Step 3: Activate Virtual Environment (if you have one)**

**If you have a `.venv` folder:**

```powershell
# PowerShell
.\.venv\Scripts\Activate.ps1

# Command Prompt
.venv\Scripts\activate.bat
```

**You should see `(.venv)` in your prompt:**
```
(.venv) PS C:\Users\57811\smartcursor>
```

**If you don't have a virtual environment, skip this step** (it's optional)

---

### **Step 4: Install Dependencies (First Time Only)**

**If this is your first time running:**

```powershell
pip install -r requirements.txt
```

This installs Flask, SQLAlchemy, and other required packages.

---

### **Step 5: Start the Server**

**Easiest Method - Use Script:**
```powershell
.\start_server.ps1
```

**OR Manual Method:**
```powershell
python -m backend.app
```

**OR if `python` doesn't work:**
```powershell
py -m backend.app
```

---

### **Step 6: Wait for Server to Start**

**You should see:**
```
[privacy] Privacy mode DISABLED - Using disk storage
[migration] phone_number column already exists in users table
[database] Database initialized at C:/Users/57811/smartcursor/data/users.db
 * Serving Flask app 'backend.app'
 * Debug mode: on
WARNING: This is a development server...
 * Running on http://0.0.0.0:5050
Press CTRL+C to quit
```

**✅ When you see `Running on http://0.0.0.0:5050`, the server is ready!**

---

### **Step 7: Open Web Frontend in Browser**

**Open your web browser** (Chrome, Edge, Firefox, etc.)

**Go to:**
```
http://127.0.0.1:5050
```

**OR:**
```
http://localhost:5050
```

**✅ You should see the Code Analysis Assistant homepage!**

---

## 📋 What You'll See in the Web UI

1. **Top Navigation Bar:**
   - Home button
   - Language selector (English/中文)
   - My Account / Logout (if logged in)
   - Login / Register (if not logged in)

2. **Main Sections:**
   - **📚 Index Repository** - Index your codebase
   - **💬 Ask Questions About Your Code** - Chat with AI about your code

3. **Features:**
   - Auto-detect analysis type (default)
   - Manual selection available
   - Generate mode for creating new projects

---

## 🛑 How to Stop the Server

1. Click on the terminal window where server is running
2. Press `Ctrl + C`
3. Server stops

**⚠️ Important:** Keep the terminal open while using the web UI. Closing it stops the server.

---

## ✅ Quick Checklist

Before starting:
- [ ] Python installed (`python --version` should work)
- [ ] In project directory (`cd C:\Users\57811\smartcursor`)
- [ ] Virtual environment activated (optional, but recommended)
- [ ] Dependencies installed (`pip install -r requirements.txt`)

To start:
- [ ] Run `python -m backend.app` or `.\start_server.ps1`
- [ ] Wait for `Running on http://0.0.0.0:5050`
- [ ] Open browser to `http://127.0.0.1:5050`

---

## 🐛 Troubleshooting

### **"python: command not found"**
```powershell
# Try using `py` instead
py -m backend.app
```

### **"ModuleNotFoundError: No module named 'flask'"**
```powershell
# Install dependencies
pip install -r requirements.txt
```

### **"Port 5050 is already in use"**
Something else is using port 5050. Find and close it, or change the port in `backend/app.py`.

### **Browser shows "This site can't be reached"**
- Make sure server is running (check terminal)
- Make sure you're using `http://127.0.0.1:5050` (not https)
- Check firewall settings

### **"Permission denied" when running PowerShell script**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 🎯 Summary

**To run and open the web UI:**

1. **Open terminal**
2. **Go to project:** `cd C:\Users\57811\smartcursor`
3. **Start server:** `python -m backend.app` or `.\start_server.ps1`
4. **Wait for:** `Running on http://0.0.0.0:5050`
5. **Open browser:** `http://127.0.0.1:5050`
6. **Keep terminal open** (server runs in that window)

**That's it!** 🎉

---

## 📱 Using the Web UI

### **Login/Register**
- Click "Login" or "Register" in top navigation
- Create account or login
- Select language preference (English/中文)

### **Index a Repository**
1. Enter repository path (e.g., `C:\Users\57811\my-portfolio`)
2. Click "Index Repository"
3. Wait for indexing to complete

### **Ask Questions**
1. Enter repository path
2. Type your question
3. (Optional) Uncheck "Auto-detect" to manually select analysis type
4. Click "Ask Question"
5. See answer with code citations

### **Generate New Project**
- Use VS Code extension command: "Generate New Project"
- Or describe project in chat with "generate" mode

---

## 💡 Pro Tips

1. **Keep server terminal visible** - You'll see logs and errors there
2. **Use Ctrl+C to stop** - Press Ctrl+C in the terminal to stop server
3. **Check server logs** - All errors and debug info appear in terminal
4. **Hard refresh browser** - Press `Ctrl+F5` if UI doesn't update

---

Enjoy using the Code Analysis Assistant! 🚀

