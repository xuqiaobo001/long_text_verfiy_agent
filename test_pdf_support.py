#!/usr/bin/env python3
"""
测试PDF支持是否正常工作
"""

import sys
from pathlib import Path
sys.path.insert(0, 'src')

def test_pdf_support():
    """测试PDF支持"""
    print("=== PDF文件支持测试 ===\n")

    try:
        from src.models.text_splitter import TextSplitter
        print("1. 检查PDF可用性:", "✅" if TextSplitter.PDF_AVAILABLE else "❌")

        # 测试PDF文件路径
        if len(sys.argv) > 1 and "test_file" in sys.argv[1]:
            test_pdf = "/root/long_text_review/test_file/test.pdf"
            if Path(test_pdf).exists():
                print(f"2. 测试PDF文件存在: {test_pdf}")
                print("3. 尝试读取PDF文件...")
                try:
                    content = TextSplitter.load_file(test_pdf)
                    print(f"4. PDF文件读取成功! 内容长度: {len(content)} 字符")
                    if len(content) > 0:
                        print("   前100字符预览:")
                        print("   " + content[:100].replace('\n', ' '))
                        return True
                    else:
                        print("   警告: PDF文件为空")
                        return True
                except Exception as e:
                    print(f"❌ 读取失败: {e}")
                    return False
            else:
                print("2. 测试PDF文件不存在，跳过文件读取测试")
                return True
        else:
            print("2. 未指定测试PDF文件，跳过文件读取测试")
            return True

    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False

if __name__ == "__main__":
    test_pdf_support()