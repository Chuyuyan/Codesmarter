# 🐛 Git Clone 错误调试指南

## 错误信息

**错误：** `tuple index out of range`
**HTTP 状态码：** 500

---

## 🔍 调试步骤

### 1. 检查服务器日志

启动服务器后，查看控制台输出，找到包含以下内容的行：
- `[clone_and_index]` 开头的日志
- Python traceback（完整的错误堆栈）

### 2. 可能的问题位置

错误 "tuple index out of range" 通常发生在：

1. **路径解析** (`entries[0]` 访问)
2. **正则表达式** (`match.group(1)` 访问)
3. **repo_id 生成** (`repo_id_from_path`)

### 3. 快速检查

```bash
# 检查 Git 是否安装
git --version

# 检查服务器日志
# 查看控制台中的 [clone_and_index] 日志
```

---

## 🔧 已应用的修复

我已经添加了以下改进：

1. ✅ **更好的错误处理** - 捕获所有异常
2. ✅ **路径验证** - 检查路径是否存在
3. ✅ **安全的目录访问** - 检查 entries 是否为空
4. ✅ **repo_id 生成改进** - 使用提供的名称或生成 UUID

---

## 🚀 测试修复

1. **重启服务器**
   ```bash
   # 停止服务器 (Ctrl+C)
   python -m backend.app
   ```

2. **再次测试 Git 克隆**
   - 使用简单的公开仓库：`https://github.com/octocat/Hello-World`
   - 不提供 token（公开仓库不需要）
   - 观察服务器日志

3. **查看详细错误**
   - 如果还有错误，服务器日志会显示完整的堆栈跟踪
   - 请提供完整的错误信息以便进一步诊断

---

## 📋 如果问题仍然存在

请提供以下信息：

1. **完整的服务器日志**
   - 特别是包含 `[clone_and_index]` 的行
   - 完整的 Python traceback

2. **使用的参数**
   - Git URL
   - Repository Name
   - Branch
   - 是否有 token

3. **系统信息**
   - Git 是否安装
   - Python 版本
   - 操作系统

---

## 💡 临时解决方案

如果 Git 克隆仍然有问题，可以使用：

1. **文件上传方式**
   - 手动克隆仓库：`git clone https://github.com/octocat/Hello-World`
   - 压缩为 ZIP
   - 使用 "Upload Folder (ZIP)" 功能

2. **使用路径方式**
   - 如果仓库已经在本地
   - 使用 "Enter Path" 标签页

