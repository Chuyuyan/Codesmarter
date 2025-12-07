# 🐳 Docker 日志查看命令（针对您的容器）

根据 `docker ps` 输出，您的容器名称是：**`smartcursor`**

## ✅ 正确的命令（直接复制使用）

### **1. 查看实时日志（推荐）**
```bash
docker logs -f smartcursor
```
**说明：** 这会实时显示日志，按 `Ctrl+C` 退出

### **2. 查看最近 200 行日志**
```bash
docker logs --tail 200 smartcursor
```

### **3. 查看最近的错误**
```bash
docker logs --tail 200 smartcursor 2>&1 | grep -i error
```

### **4. 搜索登录/认证相关日志**
```bash
docker logs smartcursor 2>&1 | grep -i -E "(login|auth|error)"
```

### **5. 查看带时间戳的最近日志**
```bash
docker logs --tail 200 -t smartcursor
```

### **6. 查看最近的登录尝试**
```bash
docker logs --tail 500 smartcursor 2>&1 | grep -i -E "(login|auth|/auth/login|/auth/me)"
```

### **7. 查看所有错误和警告**
```bash
docker logs smartcursor 2>&1 | grep -i -E "(error|warn|exception|traceback)"
```

### **8. 保存日志到文件**
```bash
docker logs smartcursor > smartcursor_logs.txt 2>&1
```

### **9. 保存最近的错误到文件**
```bash
docker logs --tail 500 smartcursor 2>&1 | grep -i error > errors.txt
```

---

## 🔍 调试登录问题的步骤

### **步骤 1：查看最近日志**
```bash
docker logs --tail 200 -t smartcursor
```

### **步骤 2：实时查看日志，然后尝试登录**
在一个终端运行：
```bash
docker logs -f smartcursor
```

在另一个终端（或浏览器）尝试登录，观察日志输出。

### **步骤 3：搜索登录相关错误**
```bash
docker logs smartcursor 2>&1 | grep -i -E "(login|auth|token|jwt|error|failed)"
```

---

## ⚠️ 常见错误

### **错误 1：使用 `<>` 符号**
❌ **错误：**
```bash
docker logs -f <container_name>
```

✅ **正确：**
```bash
docker logs -f smartcursor
```

**说明：** `<container_name>` 只是文档中的占位符，需要替换为实际容器名称。

### **错误 2：输入重定向问题**
如果在命令中看到 `-bash: syntax error near unexpected token`，通常是因为：
- 使用了 `<>` 符号（bash 会将其解释为输入重定向）
- 命令格式不正确

**解决方案：** 直接使用容器名称，不要使用任何特殊符号。

---

## 💡 快速诊断命令

### **一键查看最近的所有错误和警告**
```bash
docker logs --tail 500 smartcursor 2>&1 | grep -i -E "(error|warn|exception|traceback|failed)" | tail -50
```

### **查看最近的登录尝试（最后 50 行）**
```bash
docker logs --tail 1000 smartcursor 2>&1 | grep -i -E "(login|auth|/auth)" | tail -50
```

### **查看容器资源使用情况**
```bash
docker stats smartcursor
```

---

## 📝 如果您想查看特定时间段的日志

```bash
# 查看最近 10 分钟的日志
docker logs --since 10m smartcursor

# 查看最近 1 小时的日志
docker logs --since 1h smartcursor

# 查看今天的所有日志
docker logs --since "$(date +%Y-%m-%d)" smartcursor
```

---

## 🚀 推荐的调试流程

1. **首先查看最近日志：**
   ```bash
   docker logs --tail 200 -t smartcursor
   ```

2. **然后实时查看并尝试登录：**
   ```bash
   docker logs -f smartcursor
   ```

3. **如果看到错误，搜索相关关键词：**
   ```bash
   docker logs smartcursor 2>&1 | grep -i error
   ```

4. **保存错误日志以便分析：**
   ```bash
   docker logs --tail 1000 smartcursor > debug_logs.txt 2>&1
   ```

---

现在您可以复制上面的命令直接使用了！✅

