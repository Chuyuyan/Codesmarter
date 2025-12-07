# 🧪 如何运行文件上传测试

## 当前状态

✅ **测试文件已准备就绪**
- `test_project.zip` (0.43 KB) - 测试 ZIP 文件
- `test_upload_simple.py` - 自动化测试脚本

❌ **服务器未运行**
- 需要先启动服务器才能运行测试

---

## 🚀 方法 1：自动化测试脚本（推荐）

### 步骤：

1. **启动服务器**（在一个终端窗口）：
   ```bash
   python -m backend.app
   ```
   等待看到：
   ```
   * Running on http://127.0.0.1:5050
   ```

2. **运行测试脚本**（在另一个终端窗口）：
   ```bash
   python test_upload_simple.py
   ```

3. **查看结果**：
   - ✅ 测试 1：无认证测试（应该返回 401）
   - ✅ 测试 2：有认证测试（需要 token）

---

## 🌐 方法 2：网页界面测试（最简单）

### 步骤：

1. **启动服务器**：
   ```bash
   python -m backend.app
   ```

2. **打开浏览器**：
   - 访问：`http://127.0.0.1:5050/`

3. **登录账户**：
   - 如果没有账户，先注册
   - 登录后应该看到主页

4. **上传测试文件**：
   - 找到 "📚 Index Repository" 部分
   - 应该默认显示 **"📤 Upload Folder (ZIP)"** 标签页
   - 点击文件选择器
   - 选择 `test_project.zip`（在当前目录）
   - （可选）输入仓库名称：`test-project`
   - 点击 **"Upload and Index"** 按钮

5. **查看结果**：
   - ✅ 成功：显示绿色成功消息
   - ❌ 失败：显示红色错误消息

---

## 🔧 方法 3：使用认证 Token 测试

### 步骤：

1. **启动服务器**：
   ```bash
   python -m backend.app
   ```

2. **获取认证 Token**：
   - 打开浏览器：`http://127.0.0.1:5050/`
   - 登录账户
   - 按 F12 打开开发者工具
   - 在 Console 中输入：
     ```javascript
     localStorage.getItem('authToken')
     ```
   - 复制返回的 token

3. **设置环境变量并运行测试**：
   ```powershell
   # PowerShell
   $env:AUTH_TOKEN='your-token-here'
   python test_upload_simple.py
   ```
   
   或
   
   ```bash
   # Bash
   export AUTH_TOKEN='your-token-here'
   python test_upload_simple.py
   ```

---

## 📊 预期测试结果

### 测试 1：无认证测试
```
[OK] Correctly rejected (401 Unauthorized)
```

### 测试 2：有认证测试（如果提供 token）
```
[OK] Upload successful!
     Repository ID: test-project-api
     Chunks: 3
     Path: data/uploads/abc12345/test_upload_project
```

---

## 🐛 故障排除

### 问题 1：服务器未运行
**错误：** `Connection error: Server not running?`
**解决：** 启动服务器：`python -m backend.app`

### 问题 2：认证失败
**错误：** `401 Unauthorized`
**解决：** 确保已登录，token 有效

### 问题 3：文件未找到
**错误：** `test_project.zip not found`
**解决：** 确保在项目根目录运行测试

---

## ✅ 测试检查清单

- [ ] 服务器正在运行
- [ ] 测试文件存在（`test_project.zip`）
- [ ] 已登录账户（用于认证测试）
- [ ] 浏览器可以访问 `http://127.0.0.1:5050/`
- [ ] 上传功能正常工作
- [ ] 索引成功创建
- [ ] 可以正常提问

---

## 🎯 下一步

测试成功后，可以：
1. 尝试上传真实项目
2. 测试大文件上传（接近 100MB）
3. 测试多个仓库上传
4. 测试提问功能

