@echo off
echo =================================
echo 长文本审核Agent - Windows安装脚本
echo =================================

echo.
echo [1/6] 检查Python版本...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo Python已安装

echo.
echo [2/6] 创建虚拟环境...
if not exist venv (
    python -m venv venv
    echo 虚拟环境创建成功
) else (
    echo 虚拟环境已存在
)

echo.
echo [3/6] 激活虚拟环境...
call venv\Scripts\activate.bat
echo 虚拟环境已激活

echo.
echo [4/6] 升级pip...
python -m pip install --upgrade pip

echo.
echo [5/6] 安装依赖包...
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo 警告: 某些包安装失败，尝试使用国内镜像...
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
)

echo.
echo [6/6] 配置API密钥...
echo.
echo 请设置您的华为云MAAS API密钥:
echo 方法1: set MAAS_API_KEY=your_api_key
echo 方法2: 创建 .env 文件并添加 MAAS_API_KEY=your_api_key
echo.
echo 当前MAAS_API_KEY:
echo %MAAS_API_KEY%

echo.
echo =================================
echo 安装完成！
echo =================================
echo.
echo 下一步:
echo 1. 设置API密钥
echo 2. 运行安装检查: python install_check.py
echo 3. 查看快速开始: python examples\contract_review.py
echo.

pause