#!/usr/bin/env python3
"""
安装检查脚本
验证长文本审核Agent是否正确安装
"""

import sys
import os
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python版本过低: {version.major}.{version.minor}.{version.micro}")
        print("   需要Python 3.8或更高版本")
        return False

def check_virtual_env():
    """检查虚拟环境"""
    venv_path = Path("venv")
    if venv_path.exists():
        print("✅ 虚拟环境目录存在")

        # 检查是否在虚拟环境中
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            print("✅ 当前在虚拟环境中")
            return True
        else:
            print("⚠️  建议激活虚拟环境: source venv/bin/activate")
            return False
    else:
        print("⚠️  虚拟环境不存在，建议创建: python3 -m venv venv")
        return False

def check_dependencies():
    """检查依赖包"""
    required_packages = [
        'yaml', 'requests', 'docx', 'lxml', 'typing_extensions'
    ]
    optional_packages = ['pandas', 'openpyxl', 'aiohttp', 'redis', 'diskcache']

    missing_required = []
    missing_optional = []

    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            missing_required.append(package)
            print(f"❌ {package} (必需)")

    for package in optional_packages:
        try:
            if package == 'openpyxl':
                __import__(package)
            else:
                __import__(package)
            print(f"✅ {package} (可选)")
        except ImportError:
            missing_optional.append(package)
            print(f"⚠️  {package} (可选)")

    if missing_required:
        print(f"\n缺失必需依赖: {', '.join(missing_required)}")
        print("请运行: pip install -r requirements.txt")
        return False

    if missing_optional:
        print(f"\n可选依赖缺失: {', '.join(missing_optional)}")
        print("某些功能可能不可用")

    return len(missing_required) == 0

def check_config_files():
    """检查配置文件"""
    config_files = [
        'config/config.yaml',
        'config/review_points.yaml'
    ]

    all_exist = True
    for config_file in config_files:
        if Path(config_file).exists():
            print(f"✅ {config_file}")
        else:
            print(f"❌ {config_file} 不存在")
            all_exist = False

    return all_exist

def check_api_key():
    """检查API密钥"""
    api_key = os.getenv('MAAS_API_KEY')
    if api_key:
        print("✅ MAAS_API_KEY 环境变量已设置")
        # 检查长度（简单验证）
        if len(api_key) > 10:
            print(f"✅ API密钥长度正常 ({len(api_key)} 字符)")
            return True
        else:
            print("⚠️  API密钥可能不完整")
            return False
    else:
        print("❌ 未找到MAAS_API_KEY环境变量")
        print("请设置: export MAAS_API_KEY=your_api_key")
        return False

def check_directory_structure():
    """检查目录结构"""
    required_dirs = [
        'src',
        'src/config',
        'src/core',
        'src/models',
        'src/utils',
        'examples',
        'tests'
    ]

    all_exist = True
    for dir_path in required_dirs:
        if Path(dir_path).exists() and Path(dir_path).is_dir():
            print(f"✅ {dir_path}/")
        else:
            print(f"❌ {dir_path}/ 不存在")
            all_exist = False

    return all_exist

def check_python_files():
    """检查核心Python文件"""
    core_files = [
        'src/__init__.py',
        'src/core/reviewer.py',
        'src/models/maas_client.py',
        'src/models/text_splitter.py',
        'main.py'
    ]

    all_exist = True
    for file_path in core_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} 不存在")
            all_exist = False

    return all_exist

def test_import():
    """测试导入核心模块"""
    try:
        sys.path.insert(0, 'src')

        print("\n--- 测试模块导入 ---")

        # 测试配置管理器
        from src.config.config_manager import config_manager
        print("✅ 配置管理器导入成功")

        # 测试文本分割器
        from src.models.text_splitter import TextSplitter
        print("✅ 文本分割器导入成功")

        # 测试审核器
        from src.core.reviewer import LongTextReviewer
        print("✅ 审核器导入成功")

        return True

    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False

def main():
    """主检查函数"""
    print("=" * 50)
    print("长文本审核Agent - 安装检查")
    print("=" * 50)

    checks = [
        ("Python版本", check_python_version),
        ("虚拟环境", check_virtual_env),
        ("依赖包", check_dependencies),
        ("目录结构", check_directory_structure),
        ("核心文件", check_python_files),
        ("配置文件", check_config_files),
        ("API密钥", check_api_key),
        ("模块导入", test_import),
    ]

    results = []
    for check_name, check_func in checks:
        print(f"\n--- 检查 {check_name} ---")
        results.append((check_name, check_func()))

    # 汇总结果
    print("\n" + "=" * 50)
    print("检查结果汇总")
    print("=" * 50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for check_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{check_name:<15} : {status}")

    print(f"\n总体: {passed}/{total} 项检查通过")

    if passed == total:
        print("\n🎉 恭喜！安装成功！")
        print("\n下一步:")
        print("1. 运行示例: python examples/contract_review.py")
        print("2. 开始使用: python main.py your_file.txt")
    else:
        print(f"\n⚠️  有 {total - passed} 项检查失败")
        print("\n请参考 INSTALL.md 完成安装")

if __name__ == "__main__":
    main()