"""
长文本审核核心逻辑
整合文本分割、审核点管理和AI模型调用
"""

import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

from ..config.config_manager import config_manager
from ..config.review_points import ReviewPointsManager, ReviewIssue
from ..models.maas_client import MaaSClient
from ..models.text_splitter import TextSplitter, TextChunk
from .consistency_checker import ConsistencyChecker
from .chunk_processor import ChunkProcessor


class ReviewResult:
    """审核结果类"""

    def __init__(self):
        self.issues: List[ReviewIssue] = []
        self.suggestions: List[str] = []
        self.summary: str = ""
        self.overall_score: float = 0
        self.chunk_results: List[Dict[str, Any]] = []
        self.consistency_results: Optional[Dict[str, Any]] = None
        self.metadata: Dict[str, Any] = {}
        self.start_time: datetime = datetime.now()
        self.end_time: Optional[datetime] = None

    def add_issue(self, issue: ReviewIssue):
        """添加问题"""
        self.issues.append(issue)

    def add_issues(self, issues: List[ReviewIssue]):
        """添加多个问题"""
        self.issues.extend(issues)

    def get_issues_by_severity(self) -> Dict[str, List[ReviewIssue]]:
        """按严重程度分组问题"""
        grouped = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': []
        }

        for issue in self.issues:
            if issue.severity in grouped:
                grouped[issue.severity].append(issue)

        return grouped

    def calculate_overall_score(self):
        """计算整体评分"""
        if not self.issues:
            self.overall_score = 100
            return

        # 根据问题严重程度计算扣分
        penalty_weights = {
            'critical': 20,
            'high': 10,
            'medium': 5,
            'low': 1
        }

        total_penalty = 0
        for issue in self.issues:
            weight = penalty_weights.get(issue.severity, 1)
            confidence = issue.confidence
            total_penalty += weight * confidence

        # 计算得分，最低0分
        self.overall_score = max(0, 100 - total_penalty)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()

        return {
            'overall_score': self.overall_score,
            'issues': [issue.to_dict() for issue in self.issues],
            'issues_by_severity': {
                severity: [issue.to_dict() for issue in issues]
                for severity, issues in self.get_issues_by_severity().items()
            },
            'total_issues': len(self.issues),
            'suggestions': self.suggestions,
            'summary': self.summary,
            'chunk_results': self.chunk_results,
            'consistency_results': self.consistency_results,
            'metadata': {
                **self.metadata,
                'duration_seconds': duration,
                'start_time': self.start_time.isoformat(),
                'end_time': self.end_time.isoformat() if self.end_time else None
            }
        }


class LongTextReviewer:
    """长文本审核器"""

    def __init__(
        self,
        scenario: str = "general",
        config_dir: str = "config",
        maas_client: Optional[MaaSClient] = None
    ):
        """
        初始化长文本审核器

        Args:
            scenario: 审核场景 (contract, media, academic, general)
            config_dir: 配置目录
            maas_client: MAAS客户端实例
        """
        self.scenario = scenario
        self.logger = logging.getLogger(__name__)

        # 加载配置
        config_manager.config_dir = Path(config_dir)
        self.config = config_manager.load_config()
        review_points_config = config_manager.load_review_points()

        # 初始化组件
        self.maas_client = maas_client or self._create_maas_client()
        self.text_splitter = TextSplitter(config_manager.get_text_processing_config())
        self.review_points_manager = ReviewPointsManager(review_points_config)
        self.consistency_checker = ConsistencyChecker(self.maas_client, self.config)
        self.chunk_processor = ChunkProcessor(self.maas_client, self.config)

        # 验证配置
        if not config_manager.validate_config():
            raise ValueError("配置验证失败")

        self.logger.info(f"初始化长文本审核器，场景: {scenario}")

    def _create_maas_client(self) -> MaaSClient:
        """创建MAAS客户端"""
        maas_config = config_manager.get_maas_config()
        return MaaSClient(
            base_url=maas_config.get('base_url'),
            model=maas_config.get('model'),
            api_key=maas_config.get('api_key'),
            timeout=maas_config.get('timeout', 120),
            max_retries=maas_config.get('max_retries', 3),
            retry_delay=maas_config.get('retry_delay', 1.0)
        )

    async def review_text(
        self,
        text: str,
        context: Optional[str] = None,
        enable_consistency_check: bool = True
    ) -> ReviewResult:
        """
        审核长文本

        Args:
            text: 待审核的文本
            context: 上下文信息
            enable_consistency_check: 是否启用一致性检查

        Returns:
            审核结果
        """
        result = ReviewResult()
        result.metadata['scenario'] = self.scenario
        result.metadata['text_length'] = len(text)

        try:
            # 1. 分割文本
            self.logger.info("开始分割文本...")
            chunks = self.text_splitter.split_text(text)
            result.metadata['chunk_count'] = len(chunks)
            result.metadata['chunk_statistics'] = self.text_splitter.get_statistics(chunks)

            # 2. 并行处理各文本块
            self.logger.info(f"开始并行审核 {len(chunks)} 个文本块...")
            chunk_results = await self._process_chunks_parallel(chunks, context)
            result.chunk_results = chunk_results

            # 3. 收集问题
            for chunk_result in chunk_results:
                if 'issues' in chunk_result:
                    chunk_issues = self._parse_chunk_issues(chunk_result['issues'], chunk_result['chunk_id'])
                    result.add_issues(chunk_issues)

            # 4. 一致性检查
            if enable_consistency_check and len(chunks) > 1:
                self.logger.info("开始一致性检查...")
                consistency_result = await self.consistency_checker.check_consistency(chunks)
                result.consistency_results = consistency_result
                consistency_issues = self._parse_consistency_issues(consistency_result)
                result.add_issues(consistency_issues)

            # 5. 生成总结
            result.summary = await self._generate_summary(result)

            # 6. 计算整体评分
            result.calculate_overall_score()

            self.logger.info(f"审核完成，发现 {len(result.issues)} 个问题，整体评分: {result.overall_score}")

        except Exception as e:
            self.logger.error(f"审核过程出错: {e}")
            result.add_issue(ReviewIssue(
                chunk_id=-1,
                review_point="系统错误",
                type="error",
                severity="critical",
                description=f"审核过程出错: {str(e)}",
                location="系统",
                suggestion="请检查配置或联系技术支持"
            ))

        return result

    async def _process_chunks_parallel(
        self,
        chunks: List[TextChunk],
        context: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """并行处理文本块"""
        review_config = config_manager.get_review_config()
        parallel_config = review_config.get('parallel', {})
        max_workers = parallel_config.get('max_workers', 4)
        enable_parallel = parallel_config.get('enable_parallel', True)

        if enable_parallel and len(chunks) > 1:
            # 并行处理
            semaphore = asyncio.Semaphore(max_workers)
            tasks = [
                self._process_single_chunk_with_semaphore(semaphore, chunk, context)
                for chunk in chunks
            ]
            return await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # 串行处理
            results = []
            for chunk in chunks:
                try:
                    result = await self.chunk_processor.process_chunk(chunk, context, self.scenario)
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"处理文本块 {chunk.chunk_id} 失败: {e}")
                    results.append({
                        'chunk_id': chunk.chunk_id,
                        'error': str(e),
                        'issues': []
                    })
            return results

    async def _process_single_chunk_with_semaphore(
        self,
        semaphore: asyncio.Semaphore,
        chunk: TextChunk,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """带信号量的单块处理"""
        async with semaphore:
            return await self.chunk_processor.process_chunk(chunk, context, self.scenario)

    def _parse_chunk_issues(self, issues_data: Any, chunk_id: int) -> List[ReviewIssue]:
        """解析文本块问题"""
        issues = []

        try:
            if isinstance(issues_data, list):
                for issue_data in issues_data:
                    issue = ReviewIssue(
                        chunk_id=chunk_id,
                        review_point=issue_data.get('review_point', '未知'),
                        type=issue_data.get('type', 'general'),
                        severity=issue_data.get('severity', 'medium'),
                        description=issue_data.get('description', ''),
                        location=issue_data.get('location', f'文本块 {chunk_id}'),
                        suggestion=issue_data.get('suggestion', ''),
                        confidence=issue_data.get('confidence', 1.0)
                    )
                    issues.append(issue)

        except Exception as e:
            self.logger.error(f"解析文本块问题失败: {e}")

        return issues

    def _parse_consistency_issues(self, consistency_result: Dict[str, Any]) -> List[ReviewIssue]:
        """解析一致性问题"""
        issues = []

        try:
            if 'inconsistencies' in consistency_result:
                for inconsistency in consistency_result['inconsistencies']:
                    issue = ReviewIssue(
                        chunk_id=-1,  # 一致性问题是全局的
                        review_point="一致性检查",
                        type=inconsistency.get('type', 'consistency'),
                        severity=inconsistency.get('severity', 'high'),
                        description=inconsistency.get('description', ''),
                        location=inconsistency.get('location', '全文'),
                        suggestion=inconsistency.get('suggestion', ''),
                        confidence=inconsistency.get('confidence', 1.0)
                    )
                    issues.append(issue)

        except Exception as e:
            self.logger.error(f"解析一致性问题失败: {e}")

        return issues

    async def _generate_summary(self, result: ReviewResult) -> str:
        """生成审核总结"""
        issues_by_severity = result.get_issues_by_severity()
        total_issues = len(result.issues)

        # 构建总结
        summary_parts = [
            f"本次审核共发现 {total_issues} 个问题。",
            f"其中严重问题 {len(issues_by_severity['critical'])} 个，",
            f"重要问题 {len(issues_by_severity['high'])} 个，",
            f"一般问题 {len(issues_by_severity['medium'])} 个，",
            f"轻微问题 {len(issues_by_severity['low'])} 个。"
        ]

        # 添加一致性检查结果
        if result.consistency_results:
            consistency_score = result.consistency_results.get('consistency_score', 0)
            summary_parts.append(f"一致性评分: {consistency_score}/100。")

        # 添加整体评分
        summary_parts.append(f"整体质量评分: {result.overall_score:.1f}/100。")

        # 添加主要建议
        critical_issues = issues_by_severity['critical']
        if critical_issues:
            summary_parts.append("\n主要需要改进的问题：")
            for issue in critical_issues[:3]:  # 只显示前3个
                summary_parts.append(f"- {issue.description}")

        return ' '.join(summary_parts)

    async def review_file(
        self,
        file_path: str,
        context: Optional[str] = None,
        enable_consistency_check: bool = True
    ) -> ReviewResult:
        """
        审核文件

        Args:
            file_path: 文件路径
            context: 上下文信息
            enable_consistency_check: 是否启用一致性检查

        Returns:
            审核结果
        """
        # 加载文件内容
        text = TextSplitter.load_file(file_path)
        result = await self.review_text(text, context, enable_consistency_check)
        result.metadata['source_file'] = file_path

        return result

    def save_result(self, result: ReviewResult, output_path: str, format: str = "json"):
        """
        保存审核结果

        Args:
            result: 审核结果
            output_path: 输出路径
            format: 输出格式
        """
        output_data = result.to_dict()

        if format.lower() == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
        elif format.lower() == 'yaml':
            import yaml
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(output_data, f, allow_unicode=True, default_flow_style=False)
        else:
            raise ValueError(f"不支持的输出格式: {format}")

        self.logger.info(f"审核结果已保存到: {output_path}")

    async def close(self):
        """关闭资源"""
        if self.maas_client:
            self.maas_client.close()

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()