# 🧪 测试两种上传方式

## 📋 测试内容

1. **文件上传 (ZIP)**
   - 上传 ZIP 文件
   - 自动解压
   - 创建索引

2. **Git URL 克隆**
   - 从 Git URL 克隆仓库
   - 自动索引

---

## 🚀 测试方法 1：自动化测试脚本

### 步骤：

1. **启动服务器**
   ```bash
   python -m backend.app
   ```
   等待看到：`* Running on http://127.0.0.1:5050`

2. **登录并获取 Token**
   - 打开浏览器：`http://127.0.0.1:5050/`
   - 登录账户
   - 按 F12 打开开发者工具
   - 在 Console 中输入：
     ```javascript
     localStorage.getItem('authToken')
     ```
   - 复制返回的 token

3. **运行测试脚本**
   ```bash
   python test_both_upload_methods.py
   ```
   - 输入刚才复制的 token
   - 等待测试完成

4. **查看结果**
   - ✅ 成功：显示 "Upload successful!" 或 "Clone successful!"
   - ❌ 失败：显示错误信息

---

## 🌐 测试方法 2：网页界面测试（推荐）

### 步骤：

1. **启动服务器**
   ```bash
   python -m backend.app
   ```

2. **打开浏览器**
   - 访问：`http://127.0.0.1:5050/`

3. **测试文件上传 (ZIP)**

   a. 如果没有测试 ZIP 文件，先创建一个：
   ```bash
   # Windows PowerShell
   $testDir = "test_upload_project"
   New-Item -ItemType Directory -Path $testDir
   Set-Content -Path "$testDir\main.py" -Value "def hello():`n    print('Hello!')"
   Compress-Archive -Path "$testDir\*" -DestinationPath "test_project.zip"
   ```
   
   b. 在网页界面：
   - 登录账户
   - 找到 "📚 Index Repository" 部分
   - 点击 **"📤 Upload Folder (ZIP)"** 标签页（默认）
   - 点击 "选择文件" 或文件输入框
   - 选择 `test_project.zip`
   - （可选）输入仓库名称：`test-upload-zip`
   - 点击 **"Upload and Index"** 按钮
   - 等待完成

4. **测试 Git URL 克隆**

   a. 在网页界面：
   - 点击 **"🔗 Git URL"** 标签页
   - 输入 Git 仓库 URL：
     - 测试用：`https://github.com/octocat/Hello-World`
     - 或您自己的仓库
   - （可选）输入仓库名称：`test-clone-repo`
   - （可选）输入分支：`main`
   - 点击 **"Clone and Index"** 按钮
   - 等待完成（可能需要 1-2 分钟）

---

## ✅ 预期结果

### 文件上传成功：
```
✅ Successfully uploaded and indexed!
Found X chunks. Repository: test-upload-zip
```

### Git 克隆成功：
```
✅ Successfully cloned and indexed!
Found X chunks. Repository: test-clone-repo
```

---

## 🔍 检查清单

### 文件上传测试：
- [ ] ZIP 文件成功上传
- [ ] 文件成功解压
- [ ] 索引成功创建
- [ ] 可以正常提问
- [ ] 代码引用准确

### Git 克隆测试：
- [ ] Git 仓库成功克隆
- [ ] 索引成功创建
- [ ] 可以正常提问
- [ ] 代码引用准确
- [ ] 仓库关联到用户

---

## 🐛 常见问题

### 问题 1：服务器未运行
**错误：** `Connection refused` 或 `Failed to fetch`
**解决：** 启动服务器：`python -m backend.app`

### 问题 2：认证失败
**错误：** `401 Unauthorized`
**解决：** 确保已登录，token 有效

### 问题 3：Git 克隆失败
**错误：** `Repository not found` 或 `Authentication failed`
**解决：** 
- 检查 URL 是否正确
- 如果是私有仓库，需要提供访问令牌
- 检查网络连接

### 问题 4：Git 克隆超时
**错误：** `Request timeout`
**解决：** 
- 仓库可能太大
- 网络可能较慢
- 尝试克隆更小的仓库

### 问题 5：文件格式错误
**错误：** `Only ZIP files are supported`
**解决：** 确保上传的是 .zip 文件

---

## 📊 测试结果示例

### 成功输出：

```
============================================================
  TEST 1: File Upload (ZIP)
============================================================
[FILE] Test file: test_project.zip
       Size: 0.43 KB

[UPLOAD] Uploading test_project.zip...
[STATUS] Response: 200
[OK] Upload successful!
     Repository ID: test-upload-zip
     Chunks: 3
     Path: data/uploads/abc12345/test_upload_project

============================================================
  TEST 2: Git URL Clone
============================================================
[GIT] Repository URL: https://github.com/octocat/Hello-World

[CLONE] Cloning repository...
        This may take 1-2 minutes...
[STATUS] Response: 200
[OK] Clone successful!
     Repository ID: test-clone-hello-world
     Chunks: 5
     Path: data/clones/xyz67890/Hello-World
     Git URL: https://github.com/octocat/Hello-World

============================================================
  Test Summary
============================================================
File Upload (ZIP): [PASS]
Git URL Clone: [PASS]

Results: 2/2 tests passed

[SUCCESS] All tests passed!
```

---

## 🎯 下一步

测试成功后，可以：
1. 尝试上传真实项目
2. 测试私有仓库克隆（需要 token）
3. 测试不同分支
4. 测试提问功能
5. 测试大文件上传

---

## 📝 注意事项

1. **文件大小限制：** ZIP 文件最大 100MB
2. **Git 克隆：** 使用浅克隆（`--depth 1`），只克隆最新提交
3. **存储位置：**
   - ZIP 上传：`data/uploads/`
   - Git 克隆：`data/clones/`
4. **索引存储：** `data/index/`

---

## ✅ 完成检查

- [ ] 服务器运行正常
- [ ] 可以成功登录
- [ ] 文件上传功能正常
- [ ] Git 克隆功能正常
- [ ] 索引创建成功
- [ ] 可以正常提问
- [ ] 代码引用准确

