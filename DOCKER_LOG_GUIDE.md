# 🐳 Docker 日志查看指南

## 📋 快速查看日志命令

### **1. 查找运行中的容器**

```bash
# 查看所有运行中的容器
docker ps

# 查看所有容器（包括停止的）
docker ps -a
```

**示例输出：**
```
CONTAINER ID   IMAGE                    COMMAND                  STATUS
abc123def456   smartcursor-backend:latest   "python -m backend.app"   Up 5 minutes
```

### **2. 查看实时日志（推荐）**

```bash
# 使用容器名称
docker logs -f <container_name>

# 或使用容器 ID
docker logs -f <container_id>

# 示例
docker logs -f smartcursor-backend
docker logs -f abc123def456
```

**`-f` 参数：** 跟随日志输出（实时查看，类似 `tail -f`）

### **3. 查看最近的日志**

```bash
# 查看最后 100 行日志
docker logs --tail 100 <container_name>

# 查看最后 50 行并实时更新
docker logs --tail 50 -f <container_name>
```

### **4. 查看带时间戳的日志**

```bash
# 显示时间戳
docker logs -t <container_name>

# 实时查看带时间戳的日志
docker logs -tf <container_name>

# 查看最近 100 行并带时间戳
docker logs --tail 100 -t <container_name>
```

### **5. 查看特定时间段的日志**

```bash
# 查看最近 10 分钟的日志
docker logs --since 10m <container_name>

# 查看最近 1 小时的日志
docker logs --since 1h <container_name>

# 查看从某个时间点开始的日志
docker logs --since "2025-12-05T05:00:00" <container_name>

# 查看特定时间范围内的日志（需要结合 grep）
docker logs --since "2025-12-05T05:00:00" --until "2025-12-05T06:00:00" <container_name>
```

### **6. 搜索日志中的关键词**

```bash
# 查看包含 "error" 或 "Error" 的日志
docker logs <container_name> 2>&1 | grep -i error

# 查看登录相关的日志
docker logs <container_name> 2>&1 | grep -i login

# 查看认证相关的日志
docker logs <container_name> 2>&1 | grep -i auth

# 查看包含 "verify_user_owns_repo" 的日志
docker logs <container_name> 2>&1 | grep verify_user_owns_repo
```

---

## 🔍 调试登录问题

### **步骤 1: 查找容器**

```bash
docker ps
```

找到运行 Flask 应用的容器名称或 ID。

### **步骤 2: 查看实时日志**

```bash
# 替换 <container_name> 为您的容器名称
docker logs -f <container_name>
```

然后尝试登录，观察日志输出。

### **步骤 3: 搜索登录错误**

```bash
# 查看所有登录相关的日志
docker logs <container_name> 2>&1 | grep -i -E "(login|auth|error|failed)"

# 查看最近的错误
docker logs --tail 200 <container_name> 2>&1 | grep -i error
```

### **步骤 4: 查看认证端点日志**

```bash
# 查看 /auth/login 相关的日志
docker logs <container_name> 2>&1 | grep -i "/auth/login"

# 查看 /auth/me 相关的日志
docker logs <container_name> 2>&1 | grep -i "/auth/me"

# 查看 JWT token 相关的日志
docker logs <container_name> 2>&1 | grep -i -E "(token|jwt|bearer)"
```

---

## 📝 常见问题排查

### **问题 1: 找不到容器**

**检查：**
```bash
# 查看所有容器
docker ps -a

# 查看 Docker 镜像
docker images
```

**如果容器已停止：**
```bash
# 启动容器
docker start <container_name>

# 然后查看日志
docker logs -f <container_name>
```

### **问题 2: 日志太多，难以查找**

**解决方案：**
```bash
# 只看最近的错误
docker logs --tail 500 <container_name> 2>&1 | grep -i error

# 保存日志到文件
docker logs <container_name> > docker_logs.txt 2>&1

# 然后在文件中搜索
cat docker_logs.txt | grep -i error
```

### **问题 3: 查看特定用户的登录日志**

```bash
# 搜索用户名
docker logs <container_name> 2>&1 | grep "c29yan@uwaterloo.ca"

# 搜索用户 ID
docker logs <container_name> 2>&1 | grep "user_id"
```

---

## 🚀 Docker Compose 用户

如果您使用 `docker-compose`：

### **查看所有服务的日志**

```bash
# 查看所有服务
docker-compose logs

# 查看特定服务
docker-compose logs <service_name>

# 实时查看
docker-compose logs -f <service_name>

# 查看最近的日志
docker-compose logs --tail 100 <service_name>
```

### **示例：**

```bash
# 查看 backend 服务的日志
docker-compose logs -f backend

# 查看所有服务最近的错误
docker-compose logs --tail 200 | grep -i error
```

---

## 🔧 高级用法

### **导出日志到文件**

```bash
# 导出所有日志
docker logs <container_name> > logs_$(date +%Y%m%d_%H%M%S).txt 2>&1

# 导出最近 1000 行的日志
docker logs --tail 1000 <container_name> > recent_logs.txt 2>&1
```

### **监控日志中的多个关键词**

```bash
# 监控错误、警告和认证相关日志
docker logs -f <container_name> 2>&1 | grep -E "(ERROR|WARN|auth|login|error)"
```

### **查看日志并高亮关键词**

```bash
# 需要安装 ccze 或使用 grep 高亮
docker logs -f <container_name> 2>&1 | grep --color=always -E "(error|Error|ERROR)"
```

---

## 📊 推荐的日志查看流程

### **快速诊断登录问题：**

```bash
# 1. 找到容器
docker ps

# 2. 查看最近的日志（最后 200 行）
docker logs --tail 200 <container_name>

# 3. 实时查看日志，然后尝试登录
docker logs -f <container_name>

# 4. 如果看到错误，搜索相关关键词
docker logs <container_name> 2>&1 | grep -i -E "(error|auth|login|token)"
```

### **保存日志以便分析：**

```bash
# 保存当前日志
docker logs <container_name> > debug_$(date +%Y%m%d_%H%M%S).log 2>&1

# 或者保存最近的日志
docker logs --tail 1000 <container_name> > recent_debug.log 2>&1
```

---

## ⚠️ 常见错误模式

### **1. 导入错误（ImportError）**

```bash
# 搜索导入错误
docker logs <container_name> 2>&1 | grep -i "importerror\|modulenotfound"
```

### **2. 数据库错误**

```bash
# 搜索数据库相关错误
docker logs <container_name> 2>&1 | grep -i -E "(database|sql|db|sqlite)"
```

### **3. 认证错误**

```bash
# 搜索认证错误
docker logs <container_name> 2>&1 | grep -i -E "(unauthorized|forbidden|401|403|token)"
```

### **4. 连接错误**

```bash
# 搜索连接错误
docker logs <container_name> 2>&1 | grep -i -E "(connection|refused|timeout|cors)"
```

---

## 💡 提示

1. **使用 `-f` 参数实时查看日志** - 在另一个终端尝试登录，可以看到实时的日志输出
2. **使用 `--tail` 限制行数** - 避免日志过多难以阅读
3. **使用 `-t` 显示时间戳** - 便于定位问题发生的时间
4. **使用 `grep` 过滤日志** - 快速找到相关错误
5. **保存日志到文件** - 便于后续分析和分享

---

## 📞 如果问题仍然存在

1. **收集日志：**
   ```bash
   docker logs <container_name> > full_logs.txt 2>&1
   ```

2. **收集错误信息：**
   ```bash
   docker logs <container_name> 2>&1 | grep -i error > errors_only.txt
   ```

3. **检查容器状态：**
   ```bash
   docker ps -a
   docker inspect <container_name>
   ```

4. **查看容器资源使用：**
   ```bash
   docker stats <container_name>
   ```

---

祝您调试顺利！🚀

