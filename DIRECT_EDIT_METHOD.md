# 🔧 直接编辑方法（避免复制粘贴问题）

## 方法 1: 使用 sed 直接替换（最简单）

退出 Python（如果还在里面），然后运行：

```bash
exit()  # 如果还在 Python 中
exit    # 退出容器，回到服务器

# 在服务器上运行：
docker exec smartcursor sed -i "6s/.*const API_BASE.*/\/\/ Auto-detect API base URL based on current page/" /app/static/js/auth.js
docker exec smartcursor sed -i "7i const API_BASE = (() => {" /app/static/js/auth.js
docker exec smartcursor sed -i "8i     if (window.location.hostname !== '127.0.0.1' \&\& window.location.hostname !== 'localhost') {" /app/static/js/auth.js
docker exec smartcursor sed -i "9i         return '';" /app/static/js/auth.js
docker exec smartcursor sed -i "10i     }" /app/static/js/auth.js
docker exec smartcursor sed -i "11i     return 'http:\/\/127.0.0.1:5050';" /app/static/js/auth.js
docker exec smartcursor sed -i "12i })();" /app/static/js/auth.js
```

但这个方法太复杂了。

## 方法 2: 使用 Python -c 单行命令（推荐）

在容器内（bash，不是 Python）：

```bash
python3 -c "f=open('/app/static/js/auth.js','r');lines=f.readlines();f.close();new=[];i=0;[new.extend(['// Auto-detect API base URL based on current page\n','const API_BASE = (() => {\n','    if (window.location.hostname !== \"127.0.0.1\" and window.location.hostname != \"localhost\"):\n','        return \"\";\n','    }\n','    return \"http://127.0.0.1:5050\";\n','})();\n']) if 'const API_BASE' in l and '127.0.0.1' in l else (new.extend(['        // Use relative path if API_BASE is empty\n','        const url = API_BASE ? `${API_BASE}${endpoint}` : endpoint;\n']) if 'const url = `${API_BASE}${endpoint}`;' in l else new.append(l), setattr(sys.modules[__name__],'i',i+1)) for i,l in enumerate(lines)];f=open('/app/static/js/auth.js','w');f.writelines(new);f.close();print('Fixed!')"
```

这个方法太复杂，不可读。

## 方法 3: 创建文件并使用 Python 执行（最可靠）

在容器内：

```bash
# 创建 Python 脚本文件（逐行输入）
cat > /tmp/fix.py << 'ENDOFFILE'
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
ENDOFFILE

# 运行脚本
python3 /tmp/fix.py

# 验证
head -20 /app/static/js/auth.js
```

如果 heredoc 还是有问题，使用方法 4。

## 方法 4: 使用 nano 编辑器直接编辑（最简单直接）

在容器内：

```bash
nano /app/static/js/auth.js
```

找到第 6 行：
```
const API_BASE = 'http://127.0.0.1:5050';
```

删除这一行，替换为：
```
// Auto-detect API base URL based on current page
const API_BASE = (() => {
    if (window.location.hostname !== '127.0.0.1' && window.location.hostname !== 'localhost') {
        return '';
    }
    return 'http://127.0.0.1:5050';
})();
```

保存：Ctrl+O, Enter, Ctrl+X

