# 🔄 清除浏览器缓存 - 显示上传功能

## 🐛 问题

重新登录后，上传文件的功能（标签页）不见了。这是**浏览器缓存**问题。

---

## ✅ 快速解决方案

### **方法 1：硬刷新（最简单）** ⭐

**Windows:**
- 按 `Ctrl + F5`
- 或按 `Ctrl + Shift + R`

**Mac:**
- 按 `Cmd + Shift + R`

**这会强制浏览器重新加载所有文件！**

---

### **方法 2：通过开发者工具清除缓存**

1. 按 `F12` 打开开发者工具
2. **右键点击浏览器刷新按钮**（不要左键点击）
3. 选择 **"清空缓存并硬性重新加载"** 或 **"Empty Cache and Hard Reload"**

---

### **方法 3：手动清除缓存**

1. 按 `Ctrl + Shift + Delete` (Windows) 或 `Cmd + Shift + Delete` (Mac)
2. 选择 **"缓存的图像和文件"** 或 **"Cached images and files"**
3. 时间范围选择 **"全部时间"** 或 **"All time"**
4. 点击 **"清除数据"** 或 **"Clear data"**

---

### **方法 4：使用隐私/无痕模式**

1. 打开新的隐私/无痕窗口
   - Chrome: `Ctrl + Shift + N` (Windows) 或 `Cmd + Shift + N` (Mac)
   - Firefox: `Ctrl + Shift + P` (Windows) 或 `Cmd + Shift + P` (Mac)
2. 访问 `http://127.0.0.1:5050/`
3. 登录并测试

---

## ✅ 修复后您应该看到

修复后，界面应该显示：

1. **三个标签页按钮**：
   - 📤 Upload Folder (ZIP) ← 默认选中
   - 🔗 Git URL
   - 📁 Enter Path

2. **上传标签页内容**：
   - 文件选择器
   - Repository Name 输入框
   - "Upload and Index" 按钮

3. **Git URL 标签页内容**：
   - Git Repository URL 输入框
   - Repository Name 输入框
   - Branch 输入框
   - Access Token 输入框
   - "Clone and Index" 按钮

---

## 🔍 验证步骤

1. **硬刷新浏览器** (`Ctrl + F5`)
2. **检查是否看到标签页**
   - 应该看到三个标签按钮在顶部
3. **测试上传功能**
   - 点击 "Upload Folder (ZIP)" 标签
   - 应该看到文件选择器

---

## 📝 如果还是看不到

1. **检查浏览器控制台**（F12）
   - 查看是否有 JavaScript 错误
   - 查看 Network 标签页，检查 `index.html` 请求

2. **检查服务器日志**
   - 确认服务器正在运行
   - 查看是否有错误

3. **重启服务器**
   ```bash
   # 停止服务器 (Ctrl+C)
   python -m backend.app
   ```

---

## 🎯 推荐操作顺序

1. ✅ **硬刷新浏览器** (`Ctrl + F5`) - 最简单
2. ✅ **如果还不行，清除浏览器缓存**
3. ✅ **如果还不行，使用隐私模式测试**

---

## 💡 长期解决方案

我已经添加了**禁用缓存**的 HTTP 头，这样浏览器就不会缓存 HTML 文件了。重启服务器后，这个问题应该不会再出现。

**请重启服务器，然后硬刷新浏览器！**

