# Git忽略规则说明

## 已配置忽略的目录和文件

### 测试和数据文件
- `test_file/` - 测试文档目录
- `test_data/` - 测试数据
- `tests/data/` - 测试用例数据
- `sample_data/` - 示例数据
- `contracts/` - 合同样本
- `samples/` - 样本文档

### 生成文件和报告
- `*.xlsx` - Excel报告文件
- `*.xls` - 旧版Excel文件
- `*.csv` - CSV数据文件
- `output/` - 输出目录
- `reports/` - 报告目录
- `results/` - 结果目录

### 环境和依赖
- `venv/` - Python虚拟环境
- `.env` - 环境变量文件
- `logs/` - 日志目录
- `__pycache__/` - Python缓存

### 大文件和二进制文件
- `*.pdf`
- `*.docx`
- `*.doc`
- `*.zip`
- `*.tar.gz`
- `*.rar`
- `*.7z`

## 添加新忽略规则

如果需要忽略特定类型的文件或目录，请编辑 `.gitignore` 文件。

## 注意事项

1. 已经被git跟踪的文件，需要先使用 `git rm --cached` 移除，然后才会被忽略
2. 敏感信息（如API密钥）应该放在 `.env` 文件中
3. 大文件不应该提交到git仓库