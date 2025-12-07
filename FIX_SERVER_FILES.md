# 🔧 修复服务器上的源文件

## 问题

虽然文件复制成功了，但容器中的文件仍然是旧代码，因为**服务器上的源文件**也是旧版本。

## 解决方案

### **方法 1: 直接在容器内编辑文件（最快）**

```bash
# 1. 进入容器
docker exec -it smartcursor /bin/bash

# 2. 编辑 auth.js
nano /app/static/js/auth.js
```

找到第 6 行：
```javascript
const API_BASE = 'http://127.0.0.1:5050';
```

替换为：
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

保存（Ctrl+X, Y, Enter）

然后编辑 app.js：
```bash
nano /app/static/js/app.js
```

找到第 191-193 行附近，应该看到：
```javascript
const apiBase = (typeof API_BASE !== 'undefined' ? API_BASE : 'http://127.0.0.1:5050');
```

替换为：
```javascript
// Use relative path if API_BASE is empty (same origin), otherwise use full URL
const apiBase = (typeof API_BASE !== 'undefined' && API_BASE) ? API_BASE : '';
const endpoint = apiBase ? `${apiBase}/index_repo` : '/index_repo';
```

保存并退出容器。

### **方法 2: 使用 sed 命令批量替换（更快）**

```bash
# 在容器内直接替换 auth.js
docker exec smartcursor bash -c "cat > /app/static/js/auth.js << 'EOFAUTH'
$(cat static/js/auth.js)
EOFAUTH"

# 或者使用 sed 替换特定行
docker exec smartcursor sed -i '6s/.*/\/\/ Auto-detect API base URL based on current page\nconst API_BASE = (() => {\n    if (window.location.hostname !== \"127.0.0.1\" \&\& window.location.hostname !== \"localhost\") {\n        return \"\";\n    }\n    return \"http:\/\/127.0.0.1:5050\";\n})();/' /app/static/js/auth.js
```

### **方法 3: 更新服务器上的源文件，然后重新复制**

1. **从 Windows 复制修复后的文件到服务器**
2. **然后复制到容器**

---

## 推荐：直接在容器内编辑

这是最快的方法：

```bash
# 1. 进入容器
docker exec -it smartcursor /bin/bash

# 2. 编辑 auth.js
nano /app/static/js/auth.js
```

在文件中找到：
```javascript
const API_BASE = 'http://127.0.0.1:5050';
```

**删除这一行**，替换为：

```javascript
// Auto-detect API base URL based on current page
const API_BASE = (() => {
    if (window.location.hostname !== '127.0.0.1' && window.location.hostname !== 'localhost') {
        return '';
    }
    return 'http://127.0.0.1:5050';
})();
```

保存（Ctrl+O, Enter, Ctrl+X）

然后检查文件：
```bash
cat /app/static/js/auth.js | head -20
```

应该看到新的代码。

退出容器：
```bash
exit
```

**不需要重启容器**，因为 Flask 静态文件是直接服务的，更改会立即生效。

---

## 验证修复

1. **检查容器中的文件：**
   ```bash
   docker exec smartcursor cat /app/static/js/auth.js | head -20
   ```

2. **刷新浏览器**（Ctrl+F5）

3. **在浏览器控制台输入：**
   ```javascript
   console.log('API_BASE:', API_BASE);
   ```
   
   应该显示 `''`（空字符串）

