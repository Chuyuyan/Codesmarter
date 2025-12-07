# 🔍 检查 Git Clone 错误的步骤

## 当前错误

**错误信息：** `tuple index out of range`
**HTTP 状态码：** 500

---

## 📋 诊断步骤

### 1. 查看服务器日志

错误的具体位置应该显示在服务器控制台中。请检查：

1. **找到错误日志**
   - 在运行 `python -m backend.app` 的终端窗口
   - 查找包含 `[clone_and_index]` 的行
   - 查找包含 `Traceback` 或 `Error` 的行

2. **复制完整的错误堆栈**
   - 包括所有以 `File "...` 开头的行
   - 包括错误消息本身
   - 包括最后一行显示的错误位置

### 2. 常见的错误位置

"tuple index out of range" 可能出现在：

1. **正则表达式匹配**
   - `match.group(1)` - 如果匹配失败但代码仍尝试访问

2. **路径解析**
   - `entries[0]` - 如果目录为空
   - 路径分割操作

3. **字符串操作**
   - 字符串分割后访问索引

---

## 🔧 已应用的修复

我已经添加了：

1. ✅ 更详细的错误处理
2. ✅ 路径验证
3. ✅ 目录访问安全检查
4. ✅ 完整的错误日志记录

---

## 🚀 下一步

1. **重启服务器**
   ```bash
   # 停止当前服务器 (Ctrl+C)
   python -m backend.app
   ```

2. **再次测试 Git 克隆**
   - 使用测试仓库：`https://github.com/octocat/Hello-World`
   - 不提供 token（公开仓库）
   - 观察服务器控制台输出

3. **如果仍有错误**
   - 复制完整的服务器日志
   - 特别是包含 `[clone_and_index]` 和 `Traceback` 的部分
   - 发送给我以便进一步诊断

---

## 💡 临时解决方案

如果 Git 克隆仍有问题，可以使用：

1. **文件上传方式**
   ```bash
   # 手动克隆
   git clone https://github.com/octocat/Hello-World
   
   # 压缩
   cd Hello-World
   # Windows PowerShell:
   Compress-Archive -Path * -DestinationPath ../hello-world.zip
   
   # 然后使用网页界面上传 ZIP 文件
   ```

2. **直接提供服务器日志**
   - 这样我可以看到具体的错误位置
   - 然后进行精确修复

---

## 📝 请提供的信息

如果问题持续，请提供：

1. **完整的服务器日志**
   - 从 `[clone_and_index]` 开始到错误结束的所有行

2. **使用的参数**
   - Git URL
   - Repository Name
   - Branch
   - Token (如果有)

3. **系统信息**
   - Git 版本 (`git --version`)
   - Python 版本 (`python --version`)

