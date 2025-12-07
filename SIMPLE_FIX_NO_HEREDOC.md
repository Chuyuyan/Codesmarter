# 🚀 最简单的修复方法（不使用 heredoc）

## 方法：直接在容器内执行 Python

### **步骤 1: 进入容器**

```bash
docker exec -it smartcursor /bin/bash
```

### **步骤 2: 在容器内创建并运行 Python 脚本**

```bash
python3
```

然后粘贴以下代码（一次性粘贴）：

```python
file_path = '/app/static/js/auth.js'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
i = 0
while i < len(lines):
    if 'const API_BASE' in lines[i] and '127.0.0.1' in lines[i]:
        new_lines.append("// Auto-detect API base URL based on current page\n")
        new_lines.append("const API_BASE = (() => {\n")
        new_lines.append("    if (window.location.hostname !== '127.0.0.1' && window.location.hostname !== 'localhost') {\n")
        new_lines.append("        return '';\n")
        new_lines.append("    }\n")
        new_lines.append("    return 'http://127.0.0.1:5050';\n")
        new_lines.append("})();\n")
        i += 1
        continue
    elif 'const url = `${API_BASE}${endpoint}`;' in lines[i]:
        new_lines.append("        // Use relative path if API_BASE is empty\n")
        new_lines.append("        const url = API_BASE ? `${API_BASE}${endpoint}` : endpoint;\n")
        i += 1
        continue
    new_lines.append(lines[i])
    i += 1

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✓ Fixed!")
exit()
```

### **步骤 3: 验证**

```bash
head -20 /app/static/js/auth.js
```

### **步骤 4: 退出容器**

```bash
exit
```

---

## 或者：使用 echo 创建文件（无需 heredoc）

```bash
# 在容器内
docker exec -it smartcursor /bin/bash

# 创建 Python 文件
cat > /tmp/fix.py << 'END'
file_path = '/app/static/js/auth.js'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
new_lines = []
i = 0
while i < len(lines):
    if 'const API_BASE' in lines[i] and '127.0.0.1' in lines[i]:
        new_lines.append("// Auto-detect API base URL based on current page\n")
        new_lines.append("const API_BASE = (() => {\n")
        new_lines.append("    if (window.location.hostname !== '127.0.0.1' && window.location.hostname !== 'localhost') {\n")
        new_lines.append("        return '';\n")
        new_lines.append("    }\n")
        new_lines.append("    return 'http://127.0.0.1:5050';\n")
        new_lines.append("})();\n")
        i += 1
        continue
    elif 'const url = `${API_BASE}${endpoint}`;' in lines[i]:
        new_lines.append("        // Use relative path if API_BASE is empty\n")
        new_lines.append("        const url = API_BASE ? `${API_BASE}${endpoint}` : endpoint;\n")
        i += 1
        continue
    new_lines.append(lines[i])
    i += 1
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("Fixed!")
END

python3 /tmp/fix.py
head -20 /app/static/js/auth.js
exit
```

---

最简单：直接在 Python 交互环境中粘贴代码！

