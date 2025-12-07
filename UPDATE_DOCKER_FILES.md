# 🐳 更新 Docker 容器中的文件

## 问题

Docker 容器中的 JavaScript 文件还是旧版本，需要手动更新。

## 解决方案

### **方法 1: 使用脚本更新（推荐）**

```bash
# 给脚本添加执行权限
chmod +x UPDATE_DOCKER_FILES.sh

# 运行脚本
./UPDATE_DOCKER_FILES.sh
```

### **方法 2: 手动复制文件**

```bash
# 1. 复制 auth.js
docker cp static/js/auth.js smartcursor:/app/static/js/auth.js

# 2. 复制 app.js
docker cp static/js/app.js smartcursor:/app/static/js/app.js

# 3. 重启容器
docker restart smartcursor
```

### **方法 3: 进入容器手动编辑**

```bash
# 1. 进入容器
docker exec -it smartcursor /bin/bash

# 2. 编辑文件（在容器内）
nano /app/static/js/auth.js

# 3. 将第 6 行改为：
# const API_BASE = (() => {
#     if (window.location.hostname !== '127.0.0.1' && window.location.hostname !== 'localhost') {
#         return '';
#     }
#     return 'http://127.0.0.1:5050';
# })();

# 4. 保存并退出（Ctrl+X, Y, Enter）

# 5. 同样编辑 app.js
nano /app/static/js/app.js

# 6. 退出容器
exit

# 7. 重启容器
docker restart smartcursor
```

---

## 验证更新

### **1. 检查容器中的文件**

```bash
# 检查 auth.js 的内容
docker exec smartcursor cat /app/static/js/auth.js | head -20
```

应该看到：
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

**不应该看到：**
```javascript
const API_BASE = 'http://127.0.0.1:5050';
```

### **2. 重启容器后检查日志**

```bash
docker logs -f smartcursor
```

应该看到：
```
 * Running on http://0.0.0.0:5050
```

### **3. 在浏览器中测试**

1. **硬刷新浏览器**（Ctrl+F5）
2. **打开控制台**（F12）
3. **输入验证命令：**
   ```javascript
   console.log('API_BASE:', API_BASE);
   ```
4. **预期结果：** 应该显示 `''`（空字符串）

---

## 如果仍然不行

### **检查 1: 确认文件已更新**

```bash
docker exec smartcursor cat /app/static/js/auth.js | grep -A 10 "API_BASE"
```

### **检查 2: 清除浏览器缓存**

1. 打开开发者工具（F12）
2. 右键点击刷新按钮
3. 选择"清空缓存并硬性重新加载"

### **检查 3: 使用无痕模式**

- Chrome: `Ctrl + Shift + N`
- Firefox: `Ctrl + Shift + P`

在无痕模式下测试。

---

## 完整的更新流程

```bash
# 1. 停止容器（可选，不停止也可以）
docker stop smartcursor

# 2. 复制文件
docker cp static/js/auth.js smartcursor:/app/static/js/auth.js
docker cp static/js/app.js smartcursor:/app/static/js/app.js

# 3. 启动容器（如果之前停止了）
docker start smartcursor

# 或者重启容器（如果容器在运行）
docker restart smartcursor

# 4. 等待几秒钟让容器启动
sleep 5

# 5. 检查日志
docker logs --tail 20 smartcursor

# 6. 验证文件
docker exec smartcursor cat /app/static/js/auth.js | head -15
```

---

完成后，刷新浏览器并测试登录功能！

