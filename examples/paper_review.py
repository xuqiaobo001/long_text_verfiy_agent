#!/usr/bin/env python3
"""
学术论文审核示例
"""

import asyncio
import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.core.reviewer import LongTextReviewer
from src.utils.logger import setup_logging


async def review_paper_example():
    """学术论文审核示例"""

    # 设置日志
    setup_logging({'level': 'INFO'})

    # 示例学术论文
    paper_text = """
    摘要

    本文研究了基于深度学习的图像识别技术在自动驾驶中的应用。通过构建卷积神经网络模型，实现了对道路场景的实时识别。实验结果表明，该方法在准确率和实时性方面均优于传统方法。

    关键词：深度学习，图像识别，自动驾驶，卷积神经网络

    1. 引言

    随着人工智能技术的快速发展，自动驾驶已成为智能交通领域的研究热点。环境感知是自动驾驶的核心技术之一，其中图像识别技术扮演着重要角色[1]。

    传统的图像识别方法主要基于特征工程，需要人工设计特征提取器，这种方法存在特征表达能力有限、泛化能力差等问题[2]。

    近年来，深度学习技术在图像识别领域取得了突破性进展。Krizhevsky等人提出的AlexNet在ImageNet竞赛中取得了优异成绩[3]，开创了深度学习在图像识别领域应用的新时代。

    2. 相关工作

    2.1 传统图像识别方法

    传统方法主要包括SIFT、HOG等特征提取算法，结合SVM、随机森林等分类器。这些方法在特定场景下表现良好，但在复杂环境中的泛化能力有限。

    2.2 深度学习方法

    LeCun等人提出的卷积神经网络（CNN）是深度学习在图像处理中的典型应用[4]。通过多层卷积和池化操作，CNN能够自动学习图像的层次化特征表示。

    3. 方法

    3.1 网络架构

    我们设计了一个深度卷积神经网络，包含以下结构：
    - 输入层：接收224×224×3的RGB图像
    - 卷积层：5个卷积层，每层后接ReLU激活函数
    - 池化层：2个最大池化层，用于降采样
    - 全连接层：2个全连接层，输出1000维特征
    - 输出层：Softmax分类器，输出10个类别的概率

    3.2 训练策略

    使用随机梯度下降（SGD）优化器，学习率设置为0.01，批大小为128。采用数据增强技术，包括随机翻转、旋转等。

    4. 实验结果

    4.1 数据集

    实验使用KITTI数据集，包含7481张训练图像和7518张测试图像。

    4.2 评价指标

    使用准确率（Accuracy）、精确率（Precision）、召回率（Recall）和F1分数作为评价指标。

    4.3 结果分析

    我们的模型在测试集上取得了95.6%的准确率，相比传统方法提高了15.2%。具体结果如表1所示。

    表1：不同方法的性能比较
    | 方法 | 准确率 | 精确率 | 召回率 |
    |------|--------|--------|--------|
    | SIFT+SVM | 80.4% | 78.2% | 82.1% |
    | HOG+SVM | 82.1% | 80.5% | 83.7% |
    | 我们的方法 | 95.6% | 94.8% | 96.2% |

    5. 讨论

    实验结果表明，深度学习方法在图像识别任务中具有明显优势。这主要得益于深度网络强大的特征学习能力。

    然而，我们的方法仍存在一些局限性。首先，模型参数量大，计算资源需求高。其次，在极端天气条件下的识别准确率有待提高。

    6. 结论

    本文提出了一种基于深度学习的图像识别方法，在自动驾驶场景中取得了良好的效果。未来工作将集中在模型轻量化和鲁棒性提升方面。

    参考文献

    [1] Thrun S, Burgard W, Fox D. Probabilistic robotics[M]. MIT press, 2005.
    [2] Lowe D G. Distinctive image features from scale-invariant keypoints[J]. International journal of computer vision, 2004, 60(2): 91-110.
    [3] Krizhevsky A, Sutskever I, Hinton G E. Imagenet classification with deep convolutional neural networks[C]//Advances in neural information processing systems. 2012: 1097-1105.
    [4] LeCun Y, Bottou L, Bengio Y, et al. Gradient-based learning applied to document recognition[J]. Proceedings of the IEEE, 1998, 86(11): 2278-2324.
    """

    print("=== 学术论文审核示例 ===\n")

    # 创建审核器
    async with LongTextReviewer(scenario="academic") as reviewer:
        # 执行审核
        result = await reviewer.review_text(
            text=paper_text,
            context="这是一篇关于深度学习图像识别的学术论文",
            enable_consistency_check=True
        )

        # 输出结果
        print(f"整体评分: {result.overall_score:.1f}/100")
        print(f"发现问题: {len(result.issues)} 个")

        # 按类别显示问题
        issue_categories = {
            '结构完整性': [],
            '引用一致性': [],
            '方法描述': [],
            '数据展示': [],
            '其他': []
        }

        for issue in result.issues:
            if '结构' in issue.description or '摘要' in issue.description or '引言' in issue.description:
                issue_categories['结构完整性'].append(issue)
            elif '引用' in issue.description or '参考文献' in issue.description:
                issue_categories['引用一致性'].append(issue)
            elif '方法' in issue.description or '实验' in issue.description:
                issue_categories['方法描述'].append(issue)
            elif '数据' in issue.description or '表格' in issue.description or '图表' in issue.description:
                issue_categories['数据展示'].append(issue)
            else:
                issue_categories['其他'].append(issue)

        for category, issues in issue_categories.items():
            if issues:
                print(f"\n【{category}】({len(issues)}个问题)")
                for issue in issues[:2]:  # 只显示前2个
                    print(f"  - {issue.description} [{issue.severity}]")

        # 显示引用一致性检查
        if result.consistency_results:
            print(f"\n【引用一致性检查】")
            # 检查文内引用与参考文献的匹配情况
            citations_in_text = []
            import re
            citation_pattern = r'\[(\d+)\]'
            matches = re.findall(citation_pattern, paper_text)
            citations_in_text = [int(m) for m in matches]

            print(f"文内引用: {sorted(set(citations_in_text))}")
            print(f"参考文献: [1, 2, 3, 4]")

            # 检查是否有遗漏的引用
            all_citations = set(range(1, 5))  # 参考文献从1到4
            missing_citations = all_citations - set(citations_in_text)
            if missing_citations:
                print(f"警告: 参考文献 {sorted(missing_citations)} 在正文中未被引用")

        # 显示审核摘要
        print(f"\n【审核摘要】")
        print(result.summary)

        # 保存结果
        output_path = "output/paper_review_result.json"
        reviewer.save_result(result, output_path)
        print(f"\n详细结果已保存到: {output_path}")


if __name__ == '__main__':
    asyncio.run(review_paper_example())