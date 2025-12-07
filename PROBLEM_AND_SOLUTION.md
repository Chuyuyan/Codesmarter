# 🔍 问题分析和完整解决方案

## 📋 我们遇到的问题

### **问题 1: API_BASE 硬编码**
- **现象**: 登录时请求发送到 `http://127.0.0.1:5050/auth/login`
- **原因**: `static/js/auth.js` 中 `API_BASE` 硬编码为本地地址
- **影响**: 从公网访问时，浏览器无法连接到本地地址，导致登录失败

### **问题 2: 文件更新困难**
- **现象**: 
  - 服务器上的源文件是旧版本
  - 容器内的文件也是旧版本
  - 复制粘贴代码时 HTML `<br/>` 标签被包含进去
  - heredoc 语法在某些终端中执行失败
  - 容器内没有 nano 编辑器
- **影响**: 无法通过常规方式更新文件

### **问题 3: Python 语法错误**
- **现象**: 在 Python 交互环境中粘贴代码时出现 `invalid syntax`
- **原因**: 
  - 复制时 HTML `<br/>` 标签被包含
  - 多行代码的缩进在粘贴时可能出错
  - Python 交互环境对多行输入比较敏感

## ✅ 最简单的解决方案

### **方案 A: 从服务器复制修复后的文件（最简单）**

**步骤：**

1. **在服务器上修复源文件**（使用服务器上的编辑器）

```bash
# 在服务器上（不是容器内）
cd ~/smartcursor/Codesmarter

# 检查文件
head -10 static/js/auth.js

# 使用服务器上的编辑器（vi/vim/nano）编辑
vi static/js/auth.js
# 或
nano static/js/auth.js
```

找到第 6 行：
```javascript
const API_BASE = 'http://127.0.0.1:5050';
```

替换为：
```javascript
// Auto-detect API base URL based on current page
const API_BASE = (() => {
    if (window.location.hostname !== '127.0.0.1' && window.location.hostname !== 'localhost') {
        return '';
    }
    return 'http://127.0.0.1:5050';
})();
```

保存后，复制到容器：
```bash
docker cp static/js/auth.js smartcursor:/app/static/js/auth.js
```

2. **验证**
```bash
docker exec smartcursor head -20 /app/static/js/auth.js
```

### **方案 B: 使用 sed 命令直接替换（无需编辑器）**

在容器内运行：

```bash
# 进入容器
docker exec -it smartcursor /bin/bash

# 备份原文件
cp /app/static/js/auth.js /app/static/js/auth.js.bak

# 使用 sed 替换（需要转义特殊字符）
sed -i "6s/.*const API_BASE.*/\/\/ Auto-detect API base URL based on current page/" /app/static/js/auth.js
sed -i "7i const API_BASE = (() => {" /app/static/js/auth.js
sed -i "8i     if (window.location.hostname !== '127.0.0.1' \&\& window.location.hostname !== 'localhost') {" /app/static/js/auth.js
sed -i "9i         return '';" /app/static/js/auth.js
sed -i "10i     }" /app/static/js/auth.js
sed -i "11i     return 'http:\/\/127.0.0.1:5050';" /app/static/js/auth.js
sed -i "12i })();" /app/static/js/auth.js

# 删除原来的第 6 行（如果还在）
sed -i '/^const API_BASE = .*127.0.0.1.*$/d' /app/static/js/auth.js
```

这个方法比较复杂，因为需要处理多行。

### **方案 C: 使用 Python 脚本文件（推荐）**

在服务器上创建脚本，然后复制到容器执行：

**在服务器上：**

```bash
# 创建修复脚本
cat > /tmp/fix_auth_container.py << 'SCRIPTEND'
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
SCRIPTEND

# 复制到容器
docker cp /tmp/fix_auth_container.py smartcursor:/tmp/fix_auth_container.py

# 在容器内执行
docker exec smartcursor python3 /tmp/fix_auth_container.py

# 验证
docker exec smartcursor head -20 /app/static/js/auth.js
```

## 🎯 推荐方案

**最简单：方案 A - 在服务器上编辑文件，然后复制到容器**

原因：
1. 服务器上通常有编辑器（vi/vim/nano）
2. 不需要处理 heredoc 或 Python 交互环境
3. 可以直接看到和编辑代码
4. 复制文件到容器很简单

## 📝 完整修复步骤（方案 A）

```bash
# 1. 在服务器上编辑文件
cd ~/smartcursor/Codesmarter
vi static/js/auth.js

# 2. 在 vi 中：
#    - 按 'i' 进入编辑模式
#    - 找到第 6 行：const API_BASE = 'http://127.0.0.1:5050';
#    - 删除这一行（按 dd）
#    - 输入新代码（逐行输入）
#    - 按 Esc 退出编辑模式
#    - 输入 :wq 保存并退出

# 3. 复制到容器
docker cp static/js/auth.js smartcursor:/app/static/js/auth.js

# 4. 验证
docker exec smartcursor head -20 /app/static/js/auth.js

# 5. 刷新浏览器测试
```

