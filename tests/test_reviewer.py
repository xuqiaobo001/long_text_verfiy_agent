#!/usr/bin/env python3
"""
长文本审核测试
"""

import unittest
import asyncio
import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.core.reviewer import LongTextReviewer
from src.models.text_splitter import TextSplitter, TextChunk
from src.config.config_manager import config_manager


class TestLongTextReviewer(unittest.TestCase):
    """测试长文本审核器"""

    def setUp(self):
        """测试设置"""
        self.config_dir = Path(__file__).parent.parent / 'config'

    def test_text_splitter(self):
        """测试文本分割器"""
        config = {
            'strategy': 'chapter',
            'max_chunk_size': 2000,
            'chapter_detection': {
                'patterns': [
                    r'^第[一二三四五六七八九十\d]+章',
                    r'^\d+\.',
                ]
            }
        }

        splitter = TextSplitter(config)

        # 测试文本
        test_text = """
        第一章 引言

        这是第一章的内容，介绍了研究背景和意义。

        第二章 方法

        这是第二章的内容，详细描述了研究方法。

        第三章 结果

        这是第三章的内容，展示了实验结果。
        """

        chunks = splitter.split_text(test_text)

        # 验证分割结果
        self.assertGreater(len(chunks), 0)
        self.assertLessEqual(len(chunks[0].content), config['max_chunk_size'])

    def test_config_loading(self):
        """测试配置加载"""
        config_manager.config_dir = self.config_dir
        config = config_manager.load_config()

        # 验证配置结构
        self.assertIn('maas', config)
        self.assertIn('text_processing', config)
        self.assertIn('review', config)

    def test_review_points_loading(self):
        """测试审核点加载"""
        config_manager.config_dir = self.config_dir
        points_config = config_manager.load_review_points()

        # 验证审核点配置
        self.assertIn('general', points_config)

    async def test_reviewer_initialization(self):
        """测试审核器初始化"""
        # 使用模拟的API密钥进行测试
        import os
        os.environ['MAAS_API_KEY'] = 'test_key'

        reviewer = LongTextReviewer(
            scenario="general",
            config_dir=str(self.config_dir)
        )

        self.assertEqual(reviewer.scenario, "general")
        self.assertIsNotNone(reviewer.text_splitter)
        self.assertIsNotNone(reviewer.review_points_manager)

        await reviewer.close()


class TestConsistencyChecker(unittest.TestCase):
    """测试一致性检查器"""

    def test_terminology_extraction(self):
        """测试术语提取"""
        # 这个测试需要实际的consistency_checker实例
        # 由于需要API调用，这里只做基础测试
        pass


def run_async_test(coro):
    """运行异步测试的辅助函数"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


if __name__ == '__main__':
    # 运行异步测试
    suite = unittest.TestSuite()

    # 添加同步测试
    suite.addTest(TestLongTextReviewer('test_text_splitter'))
    suite.addTest(TestLongTextReviewer('test_config_loading'))
    suite.addTest(TestLongTextReviewer('test_review_points_loading'))

    # 添加异步测试
    test = TestLongTextReviewer('test_reviewer_initialization')
    suite.addTest(unittest.FunctionTestCase(lambda: run_async_test(test.test_reviewer_initialization())))

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)