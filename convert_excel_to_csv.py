#!/usr/bin/env python3
"""
将Excel审核报告转换为CSV格式便于查看
"""

import pandas as pd

excel_file = "/root/long_text_review/test_file/contract_audit_detailed.xlsx"
csv_file = "/root/long_text_review/test_file/contract_audit_detailed.csv"

try:
    # 读取Excel文件
    df = pd.read_excel(excel_file)

    # 保存为CSV
    df.to_csv(csv_file, index=False, encoding='utf-8-sig')

    print(f"Excel报告已转换为CSV格式: {csv_file}")
    print("\n=== 合同审核要点预览 ===")

    # 显示前20行
    print(df.head(20).to_string(index=False))

    print(f"\n=== 统计信息 ===")
    print(f"总审核要点数: {len(df)}")
    print("\n按风险等级统计:")
    print(df['风险等级'].value_counts())

    print("\n按要素类别统计:")
    print(df['要素类别'].value_counts())

except Exception as e:
    print(f"转换失败: {e}")