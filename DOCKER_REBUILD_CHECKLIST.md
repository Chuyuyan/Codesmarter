# 🐳 Docker 镜像重建检查清单

## ✅ 已修复的问题

### **1. API_BASE 硬编码问题** ✅
- **文件：** `static/js/auth.js`
- **问题：** API_BASE 硬编码为 `http://127.0.0.1:5050`，公网访问时无法连接
- **修复：** 自动检测域名，公网访问时使用相对路径（同源），本地开发时使用 `http://127.0.0.1:5050`

### **2. app.js 中的 API 调用** ✅
- **文件：** `static/js/app.js`
- **问题：** 同样硬编码了 API 地址
- **修复：** 使用相对路径，与 `auth.js` 保持一致

### **3. getAuthHeaders 导出** ✅
- **文件：** `static/js/app.js`
- **修复：** 确保 `getAuthHeaders` 函数导出到 `window` 对象

### **4. verify_user_owns_repo 导入问题** ✅
- **文件：** `backend/app.py`
- **问题：** 函数在函数内部导入，导致某些代码路径无法访问
- **修复：** 在文件顶部添加了顶层导入

---

## 📋 重建前检查

### **1. 确认所有修复已应用**

检查以下文件：

```bash
# 检查 auth.js
grep -A 5 "Auto-detect API base URL" static/js/auth.js

# 检查 app.js
grep -A 3 "Use relative path if API_BASE" static/js/app.js

# 检查 app.py
grep "from backend.modules.user_repo_helper import verify_user_owns_repo" backend/app.py
```

### **2. 验证文件内容**

**static/js/auth.js** (第 6-15 行应该类似):
```javascript
// Auto-detect API base URL based on current page
const API_BASE = (() => {
    // If running on same domain, use relative path (works for Docker/public access)
    if (window.location.hostname !== '127.0.0.1' && window.location.hostname !== 'localhost') {
        // Public access - use same origin
        return '';
    }
    // Local development
    return 'http://127.0.0.1:5050';
})();
```

**static/js/app.js** (第 191-193 行应该类似):
```javascript
// Use relative path if API_BASE is empty (same origin), otherwise use full URL
const apiBase = (typeof API_BASE !== 'undefined' && API_BASE) ? API_BASE : '';
const endpoint = apiBase ? `${apiBase}/index_repo` : '/index_repo';
```

**backend/app.py** (第 44 行应该包含):
```python
from backend.modules.user_repo_helper import verify_user_owns_repo
```

---

## 🚀 Docker 重建步骤

### **方法 1: 使用 Dockerfile 重建**

```bash
# 1. 停止并删除旧容器
docker stop smartcursor
docker rm smartcursor

# 2. 重建镜像（如果有 Dockerfile）
docker build -t smartcursor-app .

# 3. 运行新容器
docker run -d \
  --name smartcursor \
  -p 5050:5050 \
  -v /path/to/data:/app/data \
  smartcursor-app
```

### **方法 2: 直接更新文件后重启容器**

```bash
# 1. 将修复的文件复制到容器
docker cp static/js/auth.js smartcursor:/app/static/js/auth.js
docker cp static/js/app.js smartcursor:/app/static/js/app.js
docker cp backend/app.py smartcursor:/app/backend/app.py

# 2. 重启容器使更改生效
docker restart smartcursor

# 3. 查看日志确认
docker logs -f smartcursor
```

---

## ✅ 重建后测试

### **1. 检查容器状态**
```bash
docker ps | grep smartcursor
```

### **2. 查看日志**
```bash
docker logs -f smartcursor
```

应该看到：
```
[database] Database initialized at /app/data/users.db
 * Running on http://0.0.0.0:5050
```

### **3. 测试登录**
1. 打开浏览器访问您的网站
2. 打开开发者工具（F12）→ Console 标签
3. 尝试登录
4. 检查：
   - Console 是否有错误
   - Network 标签是否看到 `/auth/login` 请求
   - 服务器日志是否收到请求

### **4. 预期行为**

**公网访问时：**
- API_BASE 应该是空字符串 `''`
- 请求 URL 应该是 `/auth/login`（相对路径）
- 不应该看到 `http://127.0.0.1:5050` 的请求

**本地访问时：**
- API_BASE 应该是 `'http://127.0.0.1:5050'`
- 请求 URL 应该是 `http://127.0.0.1:5050/auth/login`

---

## 🔍 故障排除

### **问题 1: 登录仍然卡住**

**检查：**
```bash
# 查看浏览器 Console（F12）
# 查看 Network 标签中的请求
# 查看服务器日志
docker logs smartcursor 2>&1 | grep -i "auth/login"
```

**可能原因：**
- 文件没有正确复制到容器
- 浏览器缓存（尝试硬刷新 `Ctrl+F5`）
- CORS 问题

### **问题 2: 请求发送但返回错误**

**检查服务器日志：**
```bash
docker logs --tail 100 smartcursor | grep -i error
```

### **问题 3: 容器无法启动**

**检查：**
```bash
# 查看详细错误
docker logs smartcursor

# 检查容器状态
docker ps -a | grep smartcursor
```

---

## 📝 修改的文件列表

1. ✅ `static/js/auth.js` - API_BASE 自动检测
2. ✅ `static/js/app.js` - 使用相对路径，导出 getAuthHeaders
3. ✅ `backend/app.py` - 添加 verify_user_owns_repo 顶层导入

---

## 💡 提示

- **缓存问题：** 重建后，建议用户使用硬刷新（`Ctrl+F5`）清除浏览器缓存
- **日志监控：** 使用 `docker logs -f smartcursor` 实时监控日志
- **测试环境：** 先在本地测试，确认修复后再部署到生产环境

---

祝重建顺利！🚀

