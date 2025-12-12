# 快速开始指南

本指南将帮助您快速上手长文本审核Agent。

## 1. 准备工作

### 获取API密钥

1. 访问华为云MAAS平台: https://api.modelarts-maas.com
2. 注册账号并获取API密钥
3. 确保选择的模型是 **DeepSeek-V3**

### 设置环境变量

```bash
export MAAS_API_KEY=your_api_key_here
```

或创建 `.env` 文件：

```env
MAAS_API_KEY=your_api_key_here
```

## 2. 基本使用

### 审核文本文件

```bash
# 审核普通文本
python main.py document.txt

# 指定审核场景
python main.py contract.pdf -s contract

# 保存结果到指定文件
python main.py document.txt -o my_review.json
```

### 审核文本内容

```bash
# 直接传入文本内容
python main.py "这是一段需要审核的文本内容" --text
```

## 3. 场景选择

根据文档类型选择合适的场景：

- **contract**: 合同、协议、法律文档
- **media**: 新闻、文章、宣传材料
- **academic**: 论文、研究报告、学术文档
- **general**: 通用文档（默认）

## 4. 查看结果

审核完成后，您将看到：

```
=== 审核完成 ===
整体评分: 85.5/100
发现问题: 3 个
  - 严重问题: 0 个
  - 重要问题: 1 个
  - 一般问题: 2 个
  - 轻微问题: 0 个

审核摘要: 整体质量良好，建议完善部分条款...

详细结果已保存到: output/review_result.json
```

## 5. 进阶选项

### 提供上下文

```bash
python main.py document.txt --context "这是一份软件开发服务合同"
```

### 禁用一致性检查

```bash
python main.py document.txt --no-consistency
```

### 输出格式选择

```bash
# JSON格式（默认）
python main.py document.txt --format json

# YAML格式
python main.py document.txt --format yaml
```

## 6. Python API使用

```python
import asyncio
from src.core.reviewer import LongTextReviewer

async def main():
    async with LongTextReviewer(scenario="contract") as reviewer:
        # 审核文件
        result = await reviewer.review_file("contract.docx")

        # 获取问题
        for issue in result.issues:
            print(f"- {issue.description} [{issue.severity}]")

        # 保存结果
        reviewer.save_result(result, "output.json")

asyncio.run(main())
```

## 7. 运行示例

项目包含三个示例，帮助您了解不同场景的使用：

```bash
# 合同审核示例
python examples/contract_review.py

# 传媒稿件审核示例
python examples/media_review.py

# 学术论文审核示例
python examples/paper_review.py
```

## 8. 常见问题解决

### 问题：API调用失败

**解决方案**：
1. 检查API密钥是否正确设置
2. 确认网络连接正常
3. 检查API调用配额

### 问题：文件太大

**解决方案**：
系统自动处理大文件，无需担心。但可以调整配置中的 `max_chunk_size` 来优化性能。

### 问题：审核结果不准确

**解决方案**：
1. 提供详细的上下文信息
2. 选择正确的审核场景
3. 启用一致性检查

## 9. 下一步

- 阅读 [README.md](README.md) 了解详细功能
- 查看 [config/config.yaml](config/config.yaml) 自定义配置
- 编辑 [config/review_points.yaml](config/review_points.yaml) 添加审核点

## 需要帮助？

- 查看更多文档：[docs/](docs/)
- 提交问题：[GitHub Issues](link)
- 联系我们：your-email@example.com