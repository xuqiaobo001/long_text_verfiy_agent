#!/usr/bin/env python3
"""
传媒稿件审核示例
"""

import asyncio
import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.core.reviewer import LongTextReviewer
from src.utils.logger import setup_logging


async def review_media_example():
    """传媒稿件审核示例"""

    # 设置日志
    setup_logging({'level': 'INFO'})

    # 示例新闻稿件
    news_text = """
    科技创新引领未来发展

    【本报讯】记者昨日从科技部获悉，我国在人工智能领域取得重大突破。由清华大学人工智能研究院团队研发的新一代深度学习框架，在国际基准测试中获得第一名。

    据项目负责人王教授介绍，该框架在模型训练效率上比现有技术提升了3倍，能源消耗降低了50%。这一突破将为我国人工智能产业的发展提供强大技术支撑。

    产业影响深远

    业内专家指出，这一技术突破将推动多个行业的转型升级。金融、医疗、教育等领域都将从中受益。预计未来三年，相关产业规模将达到5000亿元。

    然而，也有专家提醒，技术发展需要平衡效率与安全。我们需要建立健全的监管机制，确保人工智能技术的健康发展。

    国际合作前景广阔

    在全球化背景下，科技创新需要开放合作。我国已与多个国家建立人工智能合作机制。美国、欧盟、日本等国家和地区的科研机构都表达了合作意愿。

    未来展望

    展望未来，人工智能技术将继续快速发展。我们需要在人才培养、基础研究、产业应用等方面持续发力，为建设科技强国贡献力量。

    （本文数据来源：科技部2023年度报告）
    """

    print("=== 传媒稿件审核示例 ===\n")

    # 创建审核器
    async with LongTextReviewer(scenario="media") as reviewer:
        # 执行审核
        result = await reviewer.review_text(
            text=news_text,
            context="这是一篇关于科技创新的新闻报道",
            enable_consistency_check=True
        )

        # 输出结果
        print(f"整体评分: {result.overall_score:.1f}/100")
        print(f"发现问题: {len(result.issues)} 个")

        # 按类型显示问题
        issues_by_type = {}
        for issue in result.issues:
            if issue.type not in issues_by_type:
                issues_by_type[issue.type] = []
            issues_by_type[issue.type].append(issue)

        for issue_type, issues in issues_by_type.items():
            print(f"\n【{issue_type}问题】")
            for issue in issues[:3]:  # 只显示前3个
                print(f"- {issue.description} [{issue.severity}]")

        # 显示事实检查结果
        if result.consistency_results:
            facts_result = result.consistency_results.get('detailed_results', {}).get('facts', {})
            if facts_result.get('inconsistencies'):
                print("\n【事实一致性问题】")
                for issue in facts_result['inconsistencies']:
                    print(f"- {issue['description']}")

        # 显示审核摘要
        print(f"\n【审核摘要】")
        print(result.summary)

        # 保存结果
        output_path = "output/media_review_result.json"
        reviewer.save_result(result, output_path)
        print(f"\n详细结果已保存到: {output_path}")


if __name__ == '__main__':
    asyncio.run(review_media_example())