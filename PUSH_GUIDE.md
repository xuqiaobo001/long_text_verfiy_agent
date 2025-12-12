# 推送代码到GitHub指南

## 🔐 配置GitHub认证

### 方法1: 使用Personal Access Token (推荐)

1. **创建GitHub Token**
   - 登录GitHub
   - 进入 Settings > Developer settings > Personal access tokens
   - 点击 "Generate new token"
   - 选择权限：`repo`（完整仓库访问权限）
   - 复制生成的token

2. **配置Git**
   ```bash
   git remote set-url origin https://your_token@github.com/xuqiaobo001/long_text_verfiy_agent.git
   git push origin main
   ```

### 方法2: 使用SSH密钥

1. **生成SSH密钥**
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"
   ```

2. **添加公钥到GitHub**
   - 复制 `~/.ssh/id_ed25519.pub` 内容
   - GitHub > Settings > SSH and GPG keys > New SSH key
   - 粘贴公钥内容

3. **配置远程URL为SSH**
   ```bash
   git remote set-url origin git@github.com:xuqiaobo001/long_text_verfiy_agent.git
   git push origin main
   ```

### 方法3: 使用GitHub CLI
   ```bash
   # 安装GitHub CLI
   # Windows: winget install GitHub.cli
   # macOS: brew install gh
   # Linux: sudo apt install gh

   # 登录
   gh auth login

   # 推送
   git push origin main
   ```

## 📝 已提交的更改

本次提交包含以下文件：

### 新增文件
- `INSTALL.md` - 详细安装指南
- `install_check.py` - 安装验证脚本
- `install_unix.sh` - Unix/Linux/macOS安装脚本
- `install_windows.bat` - Windows安装脚本
- `.gitignore` - Git忽略规则
- `GITIGNORE_GUIDE.md` - Git忽略说明

### 更新文件
- `README.md` - 添加文档索引和安装说明

### 删除文件
- `test_file/` 目录下的所有测试文件（已被.gitignore忽略）

## ⚡ 快速推送命令

### 使用Token推送（一次性）
```bash
# 替换your_token为您的GitHub个人访问令牌
git push https://your_token@github.com/xuqiaobo001/long_text_verfiy_agent.git main
```

## 📋 检查推送状态

```bash
# 查看提交历史
git log --oneline -5

# 查看远程分支
git remote -v

# 查看状态
git status
```

## 🆘 获取帮助

如果遇到问题：

1. **Token权限错误**
   - 确保token有`repo`权限
   - 检查token是否过期

2. **SSH认证失败**
   - 确保SSH密钥已添加到GitHub
   - 测试SSH连接: `ssh -T git@github.com`

3. **仓库不存在**
   - 确认仓库名称正确
   - 检查是否有写入权限

推送成功后，您可以在GitHub上查看：
- 完整的安装文档
- 自动化安装脚本
- 更新的README文档