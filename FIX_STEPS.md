# 🔧 修复步骤（文件路径问题）

## 问题

`/app/` 是容器内的路径，在服务器主机上不存在。需要在容器内执行命令。

## 正确的步骤

### **步骤 1: 检查容器内的文件**

```bash
# 在容器内检查文件（注意：不在服务器主机上）
docker exec smartcursor cat /app/static/js/auth.js | head -20
```

或者进入容器：
```bash
docker exec -it smartcursor /bin/bash
# 然后在容器内运行
cat /app/static/js/auth.js | head -20
```

### **步骤 2: 检查服务器上的源文件**

```bash
# 在服务器主机上检查（当前目录）
cat static/js/auth.js | head -20
```

### **步骤 3: 修复**

如果服务器上的文件是正确的，复制到容器：
```bash
docker cp static/js/auth.js smartcursor:/app/static/js/auth.js
```

如果服务器上的文件也是旧的，使用 Python 脚本修复容器内的文件：
```bash
docker exec smartcursor python3 << 'PYEOF'
import re

file_path = '/app/static/js/auth.js'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"File exists, size: {len(content)} chars")
    
    # 替换 API_BASE
    old_pattern = r"const API_BASE = 'http://127\.0\.0\.1:5050';"
    new_code = """// Auto-detect API base URL based on current page
const API_BASE = (() => {
    if (window.location.hostname !== '127.0.0.1' && window.location.hostname !== 'localhost') {
        return '';
    }
    return 'http://127.0.0.1:5050';
})();"""
    
    if re.search(old_pattern, content):
        content = re.sub(old_pattern, new_code, content)
        print("✓ Replaced API_BASE")
    elif 'Auto-detect API base URL' in content:
        print("✓ Already has auto-detect logic")
    else:
        print("⚠ Pattern not found, file might be different")
    
    # 更新 URL 构建
    if 'const url = `${API_BASE}${endpoint}`;' in content:
        content = content.replace(
            '        const url = `${API_BASE}${endpoint}`;',
            '        // Use relative path if API_BASE is empty\n        const url = API_BASE ? `${API_BASE}${endpoint}` : endpoint;'
        )
        print("✓ Updated URL construction")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✓ File updated successfully")
    
except FileNotFoundError:
    print("✗ File not found! Need to copy from server first.")
except Exception as e:
    print(f"✗ Error: {e}")
PYEOF
```

