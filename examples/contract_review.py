#!/usr/bin/env python3
"""
合同审核示例
"""

import asyncio
import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.core.reviewer import LongTextReviewer
from src.utils.logger import setup_logging


async def review_contract_example():
    """合同审核示例"""

    # 设置日志
    setup_logging({'level': 'INFO'})

    # 示例合同文本（实际使用时从文件加载）
    contract_text = """
    第一章 总则

    1.1 合同双方
    甲方：某某科技有限公司
    地址：北京市海淀区中关村大街1号
    法定代表人：张三

    乙方：某某软件开发有限公司
    地址：上海市浦东新区陆家嘴环路1000号
    法定代表人：李四

    1.2 合同标的
    乙方向甲方提供软件开发服务，包括系统设计、编码实现、测试部署等工作。

    第二章 服务内容

    2.1 开发范围
    乙方负责开发企业管理系统，包括以下模块：
    - 用户管理模块
    - 财务管理模块
    - 报表统计模块

    2.2 交付时间
    乙方应在合同签订后6个月内完成全部开发工作。

    第三章 付款方式

    3.1 合同总价
    本合同总价为人民币100万元整。

    3.2 付款进度
    甲方应按以下进度付款：
    - 合同签订后支付30%
    - 系统设计完成后支付30%
    - 系统验收后支付40%

    第四章 违约责任

    4.1 乙方违约
    如乙方未能按时交付，每逾期一日，应向甲方支付合同总价0.1%的违约金。

    4.2 甲方违约
    如甲方未能按时付款，每逾期一日，应向乙方支付应付金额0.1%的违约金。

    第五章 争议解决

    5.1 协商解决
    双方应友好协商解决合同履行过程中的争议。

    5.2 仲裁解决
    如协商不成，应提交北京仲裁委员会仲裁。

    第六章 其他条款

    6.1 合同生效
    本合同自双方签字盖章之日起生效。

    6.2 合同份数
    本合同一式四份，双方各执两份，具有同等法律效力。
    """

    print("=== 合同审核示例 ===\n")

    # 创建审核器
    async with LongTextReviewer(scenario="contract") as reviewer:
        # 执行审核
        result = await reviewer.review_text(
            text=contract_text,
            context="这是一份软件开发服务合同",
            enable_consistency_check=True
        )

        # 输出结果
        print(f"整体评分: {result.overall_score:.1f}/100")
        print(f"发现问题: {len(result.issues)} 个")

        # 按严重程度显示问题
        issues_by_severity = result.get_issues_by_severity()

        if issues_by_severity['critical']:
            print("\n【严重问题】")
            for issue in issues_by_severity['critical']:
                print(f"- {issue.description}")
                print(f"  建议: {issue.suggestion}\n")

        if issues_by_severity['high']:
            print("\n【重要问题】")
            for issue in issues_by_severity['high']:
                print(f"- {issue.description}")
                print(f"  建议: {issue.suggestion}\n")

        # 显示一致性检查结果
        if result.consistency_results:
            print(f"\n【一致性评分】: {result.consistency_results['consistency_score']:.1f}/100")
            if result.consistency_results['critical_issues']:
                print("关键一致性问题:")
                for issue in result.consistency_results['critical_issues']:
                    print(f"- {issue['description']}")

        # 显示审核摘要
        print(f"\n【审核摘要】")
        print(result.summary)

        # 保存详细结果
        output_path = "output/contract_review_result.json"
        reviewer.save_result(result, output_path)
        print(f"\n详细结果已保存到: {output_path}")


if __name__ == '__main__':
    asyncio.run(review_contract_example())