#!/usr/bin/env python3
"""
测试PDF文件审核功能示例
"""

import sys
import os
sys.path.insert(0, 'src')

from src.models.text_splitter import TextSplitter

def test_pdf_review():
    """测试PDF文件审核功能"""
    print("=== PDF文件审核功能测试 ===\n")

    # 检查测试文件
    test_file = "test_file/simple_test.pdf"
    if not os.path.exists(test_file):
        print(f"❌ 测试文件不存在: {test_file}")
        return False

    try:
        # 1. 测试PDF文件读取
        print("1. 测试PDF文件读取...")
        content = TextSplitter.load_file(test_file)
        print(f"   ✅ PDF文件读取成功，内容长度: {len(content)} 字符")
        print(f"   内容预览: {content[:100]}...\n")

        # 2. 测试文本分割
        print("2. 测试智能文本分割...")
        config = {
            "strategy": "paragraph",
            "max_chunk_size": 500,
            "chunk_overlap": 50
        }
        splitter = TextSplitter(config)
        chunks = splitter.split_text(content)
        print(f"   ✅ 文本分割成功，分割为 {len(chunks)} 个块")

        for i, chunk in enumerate(chunks[:2]):  # 显示前2个块
            print(f"   块 {i+1}: {len(chunk.content)} 字符 - {chunk.content[:50]}...")

        print()

        # 3. PDF审核准备就绪检查
        print("3. PDF审核准备就绪检查...")
        print("   ✅ PDF文件读取功能正常")
        print("   ✅ 文本分割功能正常")
        print("   📝 PDF文件已准备好进行审核处理")

        if not os.getenv('MAAS_API_KEY'):
            print("   💡 设置MAAS_API_KEY环境变量后可进行完整审核测试")

        print("\n=== PDF功能测试完成 ===")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    success = test_pdf_review()
    sys.exit(0 if success else 1)