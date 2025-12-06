# 🚀 How to Start the Server - Simple Guide

## ⚡ Quick Start (3 Steps)

### **Step 1: Open PowerShell**
- Press `Win + X`
- Click "Windows PowerShell" or "Terminal"

### **Step 2: Go to Project Folder**
```powershell
cd C:\Users\57811\smartcursor
```

### **Step 3: Start Server**
```powershell
.\start_server.ps1
```

**That's it!** ✅

---

## 📺 What You'll See

### **When Server Starts:**
```
Starting Flask server...
Open your browser at: http://127.0.0.1:5050
Press Ctrl+C to stop the server

[privacy] Privacy mode DISABLED - Using disk storage
 * Serving Flask app 'backend.app'
 * Debug mode: on
WARNING: This is a development server...
 * Running on http://0.0.0.0:5050
Press CTRL+C to quit
```

### **✅ Success!**
If you see `Running on http://0.0.0.0:5050`, the server is working!

---

## 🔍 How to Check if Server is Running

### **Open a NEW PowerShell window and run:**
```powershell
Invoke-RestMethod -Uri http://127.0.0.1:5050/health
```

### **You should see:**
```json
{
  "ok": true,
  "port": 5050
}
```

**If you see this, server is running!** ✅

---

## 🛑 How to Stop the Server

1. Click on the terminal window where server is running
2. Press `Ctrl + C`
3. Server stops

---

## ⚠️ Common Problems

### **Problem: "python: command not found"**
**Solution:** Try `py` instead of `python`:
```powershell
py -m backend.app
```

### **Problem: "ModuleNotFoundError: No module named 'flask'"**
**Solution:** Install dependencies:
```powershell
pip install -r requirements.txt
```

### **Problem: "Port 5050 is already in use"**
**Solution:** Something else is using port 5050. Close it or change port.

### **Problem: "Cannot run script" (PowerShell)**
**Solution:** Allow scripts:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 📝 Alternative Methods

### **Method 2: Batch Script**
```cmd
start_server.bat
```

### **Method 3: Manual**
```powershell
python -m backend.app
```

---

## 💡 Important Notes

1. **Keep terminal open** - Server runs in that window
2. **Don't close terminal** - Closing stops the server
3. **One server at a time** - Port 5050 can only be used by one process

---

## 🎯 Summary

**To start:**
```powershell
cd C:\Users\57811\smartcursor
.\start_server.ps1
```

**To check:**
```powershell
Invoke-RestMethod -Uri http://127.0.0.1:5050/health
```

**To stop:**
```
Press Ctrl + C
```

**That's all you need to know!** 🎉

