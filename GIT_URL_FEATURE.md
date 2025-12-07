# 🔗 Git URL 直接上传功能

## ✅ 功能已实现

现在用户可以通过**输入 Git 仓库 URL**直接克隆并索引仓库，无需下载和上传！

---

## 🎯 使用方法

### **步骤 1: 输入 Git URL**

1. 打开网页界面
2. 在 "Index Repository" 部分，点击 **"🔗 Git URL"** 标签页
3. 输入 Git 仓库 URL，例如：
   - `https://github.com/user/repo.git`
   - `https://gitlab.com/user/repo.git`
   - `https://bitbucket.org/user/repo.git`

### **步骤 2: （可选）配置**

- **仓库名称**：自定义名称（默认从 URL 提取）
- **访问令牌**：仅私有仓库需要（GitHub Personal Access Token, GitLab Token 等）

### **步骤 3: 克隆并索引**

1. 点击 **"Clone and Index"** 按钮
2. 等待克隆和索引完成
3. 成功后可以开始提问

---

## 🔧 技术实现

### **后端 (`backend/app.py`)**

新增端点：`POST /clone_and_index`

**功能：**
- ✅ 验证 Git URL 格式
- ✅ 支持公开和私有仓库
- ✅ 使用 `git clone --depth 1` 进行浅克隆（更快）
- ✅ 自动提取仓库名称
- ✅ 支持 GitHub、GitLab、Bitbucket 等
- ✅ 索引克隆的代码
- ✅ 关联到用户账户
- ✅ 错误处理（认证失败、仓库不存在等）

**支持的 Git 提供商：**
- GitHub (`github.com`)
- GitLab (`gitlab.com`)
- Bitbucket (`bitbucket.org`)
- 其他 Git 服务器（支持标准 Git URL）

**私有仓库支持：**
- GitHub: Personal Access Token (PAT)
- GitLab: OAuth Token 或 Personal Access Token
- 其他: Token 插入到 URL 中

---

### **前端 (`static/index.html`, `static/js/app.js`)**

**新增功能：**
- ✅ 第三个标签页 "🔗 Git URL"
- ✅ Git URL 输入框
- ✅ 可选的访问令牌输入（密码类型）
- ✅ URL 格式验证
- ✅ 克隆进度显示
- ✅ 双语支持（中英文）

---

## 📋 功能对比

| 功能 | 文件上传 | Git URL | 路径输入 |
|------|---------|---------|---------|
| **跨平台** | ✅ 是 | ✅ 是 | ❌ 否 |
| **需要下载** | ❌ 否 | ✅ 自动 | ❌ 否 |
| **私有仓库** | ✅ 是 | ✅ 是（需 token） | ✅ 是 |
| **实时更新** | ❌ 否 | ✅ 可 git pull | ❌ 否 |
| **适用场景** | 本地项目 | 远程仓库 | 服务器环境 |

---

## 🔐 私有仓库配置

### **GitHub**

1. 创建 Personal Access Token：
   - Settings → Developer settings → Personal access tokens → Tokens (classic)
   - 选择 `repo` 权限
   - 复制生成的 token（格式：`ghp_xxxxxxxxxxxx`）

2. 在 Git URL 标签页输入：
   - **Git URL**: `https://github.com/username/private-repo.git`
   - **Access Token**: `ghp_xxxxxxxxxxxx`

### **GitLab**

1. 创建 Personal Access Token：
   - Settings → Access Tokens
   - 选择 `read_repository` 权限
   - 复制生成的 token

2. 在 Git URL 标签页输入：
   - **Git URL**: `https://gitlab.com/username/private-repo.git`
   - **Access Token**: `your-token`

---

## ⚠️ 注意事项

1. **Git 必须安装**
   - 服务器需要安装 Git
   - 如果未安装，会显示错误消息

2. **克隆超时**
   - 大型仓库（>100MB）可能超时
   - 建议使用文件上传方式

3. **浅克隆**
   - 使用 `--depth 1` 只克隆最新提交
   - 更快，但无法访问历史记录

4. **存储位置**
   - 克隆的仓库保存在 `data/clones/` 目录
   - 每个克隆有唯一的 ID

5. **安全性**
   - Token 以密码形式输入（不显示）
   - Token 不会保存在日志中
   - 仅用于克隆，不会存储

---

## 🎨 界面预览

```
┌─────────────────────────────────────┐
│ 📚 Index Repository                  │
├─────────────────────────────────────┤
│ [📤 Upload] [🔗 Git URL] [📁 Path] │
│                                     │
│ Git Repository URL:                 │
│ [https://github.com/user/repo.git] │
│ ℹ️ Enter a public Git repository    │
│                                     │
│ Repository Name (optional):         │
│ [________________]                  │
│                                     │
│ Access Token (optional):            │
│ [••••••••••••]                      │
│ ℹ️ Required only for private repos  │
│                                     │
│ [Clone and Index]                  │
└─────────────────────────────────────┘
```

---

## 🚀 使用示例

### **公开仓库**

```
Git URL: https://github.com/facebook/react.git
Repository Name: react (可选)
Access Token: (留空)
```

### **私有仓库**

```
Git URL: https://github.com/username/private-repo.git
Repository Name: my-private-repo (可选)
Access Token: ghp_xxxxxxxxxxxx
```

---

## 🐛 常见问题

### 问题 1: "Git is not installed"
**解决：** 服务器需要安装 Git。联系管理员安装。

### 问题 2: "Authentication failed"
**解决：** 
- 检查 Git URL 是否正确
- 对于私有仓库，确保提供了有效的 token
- 检查 token 权限（需要 `repo` 或 `read_repository`）

### 问题 3: "Repository not found"
**解决：** 
- 检查 URL 是否正确
- 确保仓库存在且可访问
- 对于私有仓库，确保 token 有权限

### 问题 4: "Clone timeout"
**解决：** 
- 仓库太大，使用文件上传方式
- 或联系管理员增加超时时间

---

## ✅ 完成状态

- [x] 后端克隆端点
- [x] Git URL 验证
- [x] 私有仓库支持
- [x] 前端 UI（第三个标签页）
- [x] 错误处理
- [x] 双语支持
- [x] Token 安全输入

**功能已完全实现，可以开始使用！** 🎉

