# ✅ 最终可行的解决方案

## 问题
- 复制粘贴时 HTML `<br/>` 标签被包含
- heredoc 可能没有正确执行
- 容器内没有 nano

## 解决方案：使用 echo 创建 Python 脚本

在容器内（`root@97ae75bfe86c:/app#`），**逐行运行**以下命令：

```bash
# 1. 创建 Python 脚本文件
echo "file_path = '/app/static/js/auth.js'" > /tmp/fix.py
echo "with open(file_path, 'r', encoding='utf-8') as f:" >> /tmp/fix.py
echo "    lines = f.readlines()" >> /tmp/fix.py
echo "new_lines = []" >> /tmp/fix.py
echo "i = 0" >> /tmp/fix.py
echo "while i < len(lines):" >> /tmp/fix.py
echo "    if 'const API_BASE' in lines[i] and '127.0.0.1' in lines[i]:" >> /tmp/fix.py
echo "        new_lines.append('// Auto-detect API base URL based on current page\n')" >> /tmp/fix.py
echo "        new_lines.append('const API_BASE = (() => {\n')" >> /tmp/fix.py
echo "        new_lines.append('    if (window.location.hostname !== \"127.0.0.1\" && window.location.hostname !== \"localhost\") {\n')" >> /tmp/fix.py
echo "        new_lines.append('        return \"\";\n')" >> /tmp/fix.py
echo "        new_lines.append('    }\n')" >> /tmp/fix.py
echo "        new_lines.append('    return \"http://127.0.0.1:5050\";\n')" >> /tmp/fix.py
echo "        new_lines.append('})();\n')" >> /tmp/fix.py
echo "        i += 1" >> /tmp/fix.py
echo "        continue" >> /tmp/fix.py
echo "    elif 'const url = \`\${API_BASE}\${endpoint}\`;' in lines[i]:" >> /tmp/fix.py
echo "        new_lines.append('        // Use relative path if API_BASE is empty\n')" >> /tmp/fix.py
echo "        new_lines.append('        const url = API_BASE ? \`\${API_BASE}\${endpoint}\` : endpoint;\n')" >> /tmp/fix.py
echo "        i += 1" >> /tmp/fix.py
echo "        continue" >> /tmp/fix.py
echo "    new_lines.append(lines[i])" >> /tmp/fix.py
echo "    i += 1" >> /tmp/fix.py
echo "with open(file_path, 'w', encoding='utf-8') as f:" >> /tmp/fix.py
echo "    f.writelines(new_lines)" >> /tmp/fix.py
echo "print('Fixed!')" >> /tmp/fix.py

# 2. 运行脚本
python3 /tmp/fix.py

# 3. 验证
head -20 /app/static/js/auth.js
```

## 或者：更简单的方法 - 使用 Python 交互式

如果上面的方法太麻烦，可以：

```bash
# 进入 Python
python3

# 然后逐行输入（每行后按 Enter）：
```

然后输入：
```
file_path = '/app/static/js/auth.js'
```
按 Enter

```
with open(file_path, 'r', encoding='utf-8') as f:
```
按 Enter

```
    lines = f.readlines()
```
按 Enter（注意缩进）

继续逐行输入...

