# 🔧 修复容器内的 backend/app.py

## 问题

容器内的 `backend/app.py` 是旧版本，还在使用 `verify_user_owns_repo`，但函数没有导入，导致 500 错误。

## 解决方案

### **步骤 1: 复制更新后的文件到容器**

```bash
# 在服务器上（确保在正确的目录）
cd ~/smartcursor/Codesmarter

# 复制更新后的 app.py 到容器
docker cp backend/app.py smartcursor:/app/backend/app.py
```

### **步骤 2: 重启容器**

```bash
docker restart smartcursor
```

### **步骤 3: 等待容器启动（约 10 秒）**

```bash
# 查看日志确认启动成功
docker logs --tail 20 smartcursor
```

应该看到：
```
 * Running on http://0.0.0.0:5050
```

### **步骤 4: 验证修复**

```bash
# 检查容器内的文件是否有导入
docker exec smartcursor grep "from backend.modules.user_repo_helper import verify_user_owns_repo" /app/backend/app.py
```

应该看到：
```
from backend.modules.user_repo_helper import verify_user_owns_repo
```

### **步骤 5: 测试**

刷新浏览器，再次尝试 index repo。

---

## 如果文件路径不对

如果 `backend/app.py` 不在 `~/smartcursor/Codesmarter/backend/app.py`，找到正确路径：

```bash
# 查找 app.py
find ~/smartcursor -name "app.py" -path "*/backend/app.py"
```

然后使用找到的路径复制。

---

## 验证修复

修复后，再次尝试 index repo，应该不再出现 500 错误。

如果还有问题，查看日志：
```bash
docker logs --tail 50 smartcursor | grep -i error
```

