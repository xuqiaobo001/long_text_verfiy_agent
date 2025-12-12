#!/bin/bash

echo "=================================="
echo "长文本审核Agent - Unix/Linux/macOS 安装脚本"
echo "=================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 函数：打印成功信息
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# 函数：打印警告信息
warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 函数：打印错误信息
error() {
    echo -e "${RED}❌ $1${NC}"
}

# 1. 检查Python版本
echo "[1/6] 检查Python版本..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    if [ "$(echo "$PYTHON_VERSION >= 3.8" | bc -l)" -eq 1 ] 2>/dev/null || [ "${PYTHON_VERSION%.*}" = "3.8" ] || [ "${PYTHON_VERSION%.*}" = "3.9" ] || [ "${PYTHON_VERSION%.*}" = "3.10" ] || [ "${PYTHON_VERSION%.*}" = "3.11" ]; then
        success "Python $PYTHON_VERSION 已安装"
    else
        error "Python版本过低: $PYTHON_VERSION (需要3.8+)"
        echo "请升级Python或使用pyenv管理多版本"
        exit 1
    fi
else
    error "未找到Python3，请先安装"
    echo "Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "CentOS/RHEL: sudo yum install python3 python3-pip"
    echo "macOS: brew install python3"
    exit 1
fi

# 2. 创建虚拟环境
echo ""
echo "[2/6] 创建虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    success "虚拟环境创建成功"
else
    warning "虚拟环境已存在"
fi

# 3. 激活虚拟环境
echo ""
echo "[3/6] 激活虚拟环境..."
source venv/bin/activate
success "虚拟环境已激活"

# 4. 升级pip
echo ""
echo "[4/6] 升级pip..."
python -m pip install --upgrade pip --quiet
success "pip已升级到最新版本"

# 5. 安装依赖
echo ""
echo "[5/6] 安装依赖包..."
if pip install -r requirements.txt; then
    success "所有依赖包安装成功"
else
    warning "某些包安装失败，尝试使用国内镜像..."
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
fi

# 6. 配置API密钥
echo ""
echo "[6/6] 配置API密钥..."
if [ -z "$MAAS_API_KEY" ]; then
    warning "未找到MAAS_API_KEY环境变量"
    echo ""
    echo "请设置您的华为云MAAS API密钥："
    echo "方法1: export MAAS_API_KEY=your_api_key"
    echo "方法2: echo \"MAAS_API_KEY=your_api_key\" > .env"
    echo ""
    echo "获取API密钥请访问: https://api.modelarts-maas.com"
else
    success "MAAS_API_KEY已设置"
fi

# 安装完成
echo ""
echo "=================================="
echo "安装完成！"
echo "=================================="
echo ""
echo "下一步操作:"
echo "1. 设置API密钥（如果尚未设置）"
echo "2. 运行安装检查:"
echo "   python install_check.py"
echo "3. 查看快速开始:"
echo "   python examples/contract_review.py"
echo ""
echo "如需帮助，请查看:"
echo "- 安装指南: INSTALL.md"
echo "- 快速开始: QUICKSTART.md"
echo ""

# 可选：运行安装检查
read -p "是否立即运行安装检查？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "运行安装检查..."
    python install_check.py
fi

echo "安装脚本执行完成！"