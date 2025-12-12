# 长文本审核Agent - 安装指导

本文档将指导您完成长文本审核Agent的完整安装和配置过程。

## 📋 系统要求

### 最低要求
- **Python**: 3.8 或更高版本
- **内存**: 至少 4GB RAM
- **磁盘空间**: 500MB 可用空间
- **网络**: 稳定的互联网连接（用于调用AI服务）

### 推荐配置
- **Python**: 3.9-3.11
- **内存**: 8GB 或更多
- **CPU**: 多核处理器（支持并行处理）
- **系统**: Linux/macOS/Windows

## 🚀 快速安装（推荐）

### 1. 克隆项目
```bash
# 使用git克隆
git clone https://github.com/your-repo/long_text_review.git
cd long_text_review

# 或者下载并解压
# https://github.com/your-repo/long_text_review/archive/main.zip
```

### 2. 创建虚拟环境
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# Linux/macOS:
source venv/bin/activate

# Windows:
# venv\Scripts\activate
```

### 3. 安装依赖
```bash
# 安装所有依赖
pip install -r requirements.txt

# 如果遇到依赖问题，尝试更新pip
pip install --upgrade pip
```

### 4. 配置API密钥
```bash
# 创建环境变量文件
echo "MAAS_API_KEY=your_api_key_here" > .env

# 或者直接设置环境变量
export MAAS_API_KEY=your_api_key_here
```

### 5. 验证安装
```bash
# 运行测试
python examples/contract_review.py

# 如果看到审核输出，说明安装成功！
```

## 📦 详细安装步骤

### 步骤 1: 环境准备

#### 1.1 安装Python
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv

# CentOS/RHEL
sudo yum install python3 python3-pip

# macOS (使用Homebrew)
brew install python3

# Windows
# 下载并安装 https://www.python.org/downloads/
```

#### 1.2 验证Python版本
```bash
python3 --version
# 应该显示: Python 3.x.x 或更高
```

### 步骤 2: 获取项目代码

#### 2.1 通过Git克隆（推荐）
```bash
git clone https://github.com/your-repo/long_text_review.git
cd long_text_review
```

#### 2.2 直接下载
1. 访问项目GitHub页面
2. 点击 "Code" -> "Download ZIP"
3. 解压到合适的目录
4. 进入解压后的目录

### 步骤 3: 创建Python虚拟环境

#### 3.1 创建虚拟环境
```bash
python3 -m venv venv
```

#### 3.2 激活虚拟环境
```bash
# Linux/macOS:
source venv/bin/activate

# Windows Command Prompt:
venv\Scripts\activate.bat

# Windows PowerShell:
venv\Scripts\Activate.ps1
```

#### 3.3 验证激活
```bash
# 应该看到 (venv) 前缀
which python
# 应该指向 venv 目录中的python
```

### 步骤 4: 安装依赖包

#### 4.1 升级pip
```bash
pip install --upgrade pip
```

#### 4.2 安装项目依赖
```bash
# 从requirements.txt安装
pip install -r requirements.txt
```

#### 4.3 验证关键依赖
```bash
# 测试python-docx
python -c "import docx; print('python-docx OK')"

# 测试requests
python -c "import requests; print('requests OK')"

# 测试PyYAML
python -c "import yaml; print('PyYAML OK')"
```

### 步骤 5: 配置系统

#### 5.1 获取华为云MAAS API密钥
1. 访问华为云MAAS平台: https://api.modelarts-maas.com
2. 注册账号并登录
3. 创建新项目或使用现有项目
4. 获取API密钥（通常在API管理页面）

#### 5.2 配置API密钥
```bash
# 方法1: 创建.env文件（推荐）
echo "MAAS_API_KEY=your_actual_api_key" > .env

# 方法2: 设置环境变量
export MAAS_API_KEY=your_actual_api_key

# 方法3: Windows用户
set MAAS_API_KEY=your_actual_api_key
```

#### 5.3 测试API连接
```python
# 创建测试文件 test_api.py
import sys
sys.path.insert(0, 'src')
from src.models.maas_client import MaaSClient

try:
    client = MaaSClient()
    print("MAAS客户端创建成功！")
except Exception as e:
    print(f"API连接失败: {e}")
```

```bash
python test_api.py
```

### 步骤 6: 运行示例

#### 6.1 使用命令行工具
```bash
# 审核合同示例
python main.py examples/sample_contract.txt -s contract

# 审核传媒稿件示例
python main.py examples/sample_news.txt -s media

# 查看帮助
python main.py --help
```

#### 6.2 运行Python示例
```bash
# 合同审核示例
python examples/contract_review.py

# 传媒稿件审核示例
python examples/media_review.py

# 学术论文审核示例
python examples/paper_review.py
```

## ⚙️ 高级配置

### 自定义配置文件
```bash
# 复制默认配置
cp config/config.yaml config/config.local.yaml

# 编辑本地配置
nano config/config.local.yaml
```

### 配置并发处理数
编辑 `config/config.yaml`:
```yaml
review:
  parallel:
    max_workers: 8  # 根据CPU核心数调整
    enable_parallel: true
```

### 配置文本分割策略
```yaml
text_processing:
  chunking:
    strategy: "chapter"  # chapter/paragraph/semantic/fixed_size
    max_chunk_size: 12000  # 根据文档复杂度调整
    chunk_overlap: 200
```

## 🔧 常见问题解决

### 问题1: Python版本不兼容
```bash
# 解决方案：使用conda或pyenv
# 使用pyenv管理多版本Python
curl https://pyenv.run | bash
pyenv install 3.9.16
pyenv local 3.9.16
```

### 问题2: 依赖安装失败
```bash
# 升级pip和setuptools
pip install --upgrade pip setuptools wheel

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题3: python-docx安装失败
```bash
# Ubuntu/Debian安装依赖
sudo apt-get install python3-dev libxml2-dev libxslt1-dev zlib1g-dev

# 然后重试
pip install python-docx
```

### 问题4: API调用失败
```bash
# 检查网络连接
curl -I https://api.modelarts-maas.com

# 检查API密钥
echo $MAAS_API_KEY

# 查看详细错误日志
python main.py your_file.txt --debug
```

### 问题5: 内存不足
```bash
# 减少并行worker数量
# 编辑 config/config.yaml
review:
  parallel:
    max_workers: 2  # 减少并发数

# 或者减小chunk大小
text_processing:
  chunking:
    max_chunk_size: 4000
```

## 📝 安装验证清单

完成安装后，请确认以下各项：

- [ ] Python 3.8+ 已安装
- [ ] 虚拟环境已创建并激活
- [ ] 所有依赖包已安装
- [ ] API密钥已配置
- [ ] 测试示例可以正常运行
- [ ] 日志输出正常
- [ ] 审核报告可以正常生成

## 📚 后续配置

### 1. 日志配置
```yaml
logging:
  level: "INFO"
  file: "logs/app.log"
  max_file_size: "10MB"
  backup_count: 5
```

### 2. 缓存配置（可选）
```yaml
cache:
  enable: true
  type: "file"  # 或 redis
  ttl: 3600
  max_size: 1000
```

### 3. 性能优化
```yaml
maas:
  timeout: 120
  max_retries: 3
  retry_delay: 1.0

review:
  parallel:
    max_workers: 4  # 根据CPU核心数调整
    enable_parallel: true
```

## 🆘 获取帮助

如果遇到问题：

1. **查看文档**:
   - [README.md](README.md) - 项目概述
   - [QUICKSTART.md](QUICKSTART.md) - 快速开始

2. **检查日志**:
   ```bash
   tail -f logs/app.log
   ```

3. **运行测试**:
   ```bash
   python tests/test_reviewer.py
   ```

4. **报告问题**:
   - GitHub Issues: https://github.com/your-repo/issues
   - 邮箱: support@example.com

## ✅ 安装完成

恭喜！您已经成功安装了长文本审核Agent。现在可以开始：

1. 运行 `python main.py --help` 查看所有选项
2. 尝试运行示例代码
3. 使用自己的文档进行测试
4. 根据需要调整配置

祝您使用愉快！🎉