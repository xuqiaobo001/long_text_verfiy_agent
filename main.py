#!/usr/bin/env python3
"""
长文本审核Agent主程序
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.config.config_manager import config_manager
from src.core.reviewer import LongTextReviewer
from src.utils.logger import setup_logging, get_logger


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='长文本审核Agent')
    parser.add_argument('input', help='输入文件路径或文本内容')
    parser.add_argument('-o', '--output', help='输出文件路径', default='output/review_result.json')
    parser.add_argument('-s', '--scenario', choices=['general', 'contract', 'media', 'academic'],
                       default='general', help='审核场景')
    parser.add_argument('-c', '--config', default='config', help='配置目录')
    parser.add_argument('--no-consistency', action='store_true', help='禁用一致性检查')
    parser.add_argument('--context', help='额外的上下文信息')
    parser.add_argument('--format', choices=['json', 'yaml'], default='json', help='输出格式')
    parser.add_argument('--text', action='store_true', help='输入是直接文本而非文件路径')

    args = parser.parse_args()

    # 设置日志
    config_manager.config_dir = Path(args.config)
    config = config_manager.load_config()
    setup_logging(config.get('logging', {}))
    logger = get_logger(__name__)

    try:
        # 创建审核器
        async with LongTextReviewer(scenario=args.scenario, config_dir=args.config) as reviewer:
            logger.info(f"开始审核，场景: {args.scenario}")

            # 获取输入内容
            if args.text:
                text = args.input
                logger.info(f"文本长度: {len(text)} 字符")
            else:
                text = reviewer.text_splitter.load_file(args.input)
                logger.info(f"文件: {args.input}")
                logger.info(f"文本长度: {len(text)} 字符")

            # 执行审核
            result = await reviewer.review_text(
                text=text,
                context=args.context,
                enable_consistency_check=not args.no_consistency
            )

            # 保存结果
            reviewer.save_result(result, args.output, args.format)

            # 输出摘要
            print(f"\n=== 审核完成 ===")
            print(f"整体评分: {result.overall_score:.1f}/100")
            print(f"发现问题: {len(result.issues)} 个")
            issues_by_severity = result.get_issues_by_severity()
            print(f"  - 严重问题: {len(issues_by_severity['critical'])} 个")
            print(f"  - 重要问题: {len(issues_by_severity['high'])} 个")
            print(f"  - 一般问题: {len(issues_by_severity['medium'])} 个")
            print(f"  - 轻微问题: {len(issues_by_severity['low'])} 个")
            print(f"\n审核摘要: {result.summary}")
            print(f"\n详细结果已保存到: {args.output}")

    except Exception as e:
        logger.error(f"审核失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())