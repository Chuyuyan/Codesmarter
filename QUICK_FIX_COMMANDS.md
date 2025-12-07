# 🚀 快速修复命令（容器内没有编辑器的情况）

## 问题
容器内的编辑器显示为空，或者文件内容不对。

## 解决方案：使用命令行直接修复

### **方法 1: 使用 Python 脚本修复（推荐）**

在服务器上运行：
```bash
bash fix_container_auth.sh
```

### **方法 2: 手动使用 Python 修复**

退出容器（如果还在里面），然后运行：

```bash
# 使用 Python 修复文件
docker exec smartcursor python3 << 'PYEOF'
import re

file_path = '/app/static/js/auth.js'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 替换 API_BASE 定义
old_pattern = r"const API_BASE = 'http://127\.0\.0\.1:5050';"
new_code = """// Auto-detect API base URL based on current page
const API_BASE = (() => {
    if (window.location.hostname !== '127.0.0.1' && window.location.hostname !== 'localhost') {
        return '';
    }
    return 'http://127.0.0.1:5050';
})();"""

content = re.sub(old_pattern, new_code, content)

# 更新 URL 构建逻辑
if 'const url = `${API_BASE}${endpoint}`;' in content:
    content = content.replace(
        'const url = `${API_BASE}${endpoint}`;',
        '// Use relative path if API_BASE is empty\n        const url = API_BASE ? `${API_BASE}${endpoint}` : endpoint;'
    )

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ File fixed successfully!")
PYEOF

# 验证
docker exec smartcursor head -20 /app/static/js/auth.js
```

### **方法 3: 使用 sed 命令（如果 Python 不可用）**

```bash
# 先备份
docker exec smartcursor cp /app/static/js/auth.js /app/static/js/auth.js.backup

# 使用 sed 替换（需要转义特殊字符）
docker exec smartcursor sed -i "6s/.*/\/\/ Auto-detect API base URL based on current page/" /app/static/js/auth.js
docker exec smartcursor sed -i "7s/.*/const API_BASE = (() => {/" /app/static/js/auth.js
docker exec smartcursor sed -i "8s/.*/    if (window.location.hostname !== '127.0.0.1' \&\& window.location.hostname !== 'localhost') {/" /app/static/js/auth.js
docker exec smartcursor sed -i "9s/.*/        return '';/" /app/static/js/auth.js
docker exec smartcursor sed -i "10s/.*/    }/" /app/static/js/auth.js
docker exec smartcursor sed -i "11s/.*/    return 'http:\/\/127.0.0.1:5050';/" /app/static/js/auth.js
docker exec smartcursor sed -i "12s/.*/})();/" /app/static/js/auth.js
```

### **方法 4: 直接从服务器复制修复后的文件**

如果您在服务器上有修复后的文件：

```bash
# 确保您在正确的目录
cd ~/smartcursor

# 检查本地文件是否正确
head -20 static/js/auth.js

# 如果本地文件正确，复制到容器
docker cp static/js/auth.js smartcursor:/app/static/js/auth.js

# 验证
docker exec smartcursor head -20 /app/static/js/auth.js
```

---

## 如果文件真的为空或不存在

### 检查文件：
```bash
docker exec smartcursor ls -la /app/static/js/
docker exec smartcursor cat /app/static/js/auth.js
```

### 如果文件不存在，从服务器复制：
```bash
# 确保服务器上有正确的文件
cd ~/smartcursor
ls -la static/js/auth.js

# 复制到容器
docker cp static/js/auth.js smartcursor:/app/static/js/auth.js
```

---

## 推荐流程

1. **先检查文件内容：**
   ```bash
   docker exec smartcursor head -10 /app/static/js/auth.js
   ```

2. **如果文件存在但有旧代码，使用方法 2（Python 脚本）**

3. **如果文件为空，从服务器复制：**
   ```bash
   cd ~/smartcursor
   docker cp static/js/auth.js smartcursor:/app/static/js/auth.js
   ```

4. **验证修复：**
   ```bash
   docker exec smartcursor head -20 /app/static/js/auth.js
   ```

5. **刷新浏览器测试**

---

完成后，不需要重启容器，刷新浏览器即可！

