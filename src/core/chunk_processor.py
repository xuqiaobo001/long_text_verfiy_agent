"""
文本块处理器
处理单个文本块的审核
"""

import logging
import json
from typing import Dict, Any, Optional, List

from ..config.review_points import ReviewPointsManager
from ..models.text_splitter import TextChunk
from ..models.maas_client import MaaSClient


class ChunkProcessor:
    """文本块处理器"""

    def __init__(self, maas_client: MaaSClient, config: Dict[str, Any]):
        """
        初始化文本块处理器

        Args:
            maas_client: MAAS客户端
            config: 配置信息
        """
        self.maas_client = maas_client
        self.config = config
        self.logger = logging.getLogger(__name__)

        # 审核点管理器会在reviewer中传入
        self.review_points_manager = None

    async def process_chunk(
        self,
        chunk: TextChunk,
        context: Optional[str] = None,
        scenario: str = "general"
    ) -> Dict[str, Any]:
        """
        处理单个文本块

        Args:
            chunk: 文本块
            context: 上下文信息
            scenario: 审核场景

        Returns:
            处理结果
        """
        try:
            # 获取该场景的局部审核点
            if self.review_points_manager:
                review_points = self.review_points_manager.get_local_check_points(scenario)
            else:
                review_points = []

            # 生成审核提示
            review_prompt = self.review_points_manager.generate_review_prompt(review_points) if review_points else self._generate_default_review_prompt()

            # 构建完整的上下文
            full_context = self._build_context(chunk, context, scenario)

            # 调用AI模型进行审核
            response = await self._review_with_ai(chunk.content, full_context, review_prompt)

            # 解析响应
            result = self._parse_ai_response(response, chunk.chunk_id)

            # 添加文本块信息
            result['chunk_id'] = chunk.chunk_id
            result['chapter'] = chunk.chapter
            result['section'] = chunk.section
            result['content_length'] = len(chunk.content)

            return result

        except Exception as e:
            self.logger.error(f"处理文本块 {chunk.chunk_id} 失败: {e}")
            return {
                'chunk_id': chunk.chunk_id,
                'error': str(e),
                'issues': [],
                'overall_score': 0,
                'suggestions': [f"处理失败: {str(e)}"]
            }

    def _build_context(
        self,
        chunk: TextChunk,
        external_context: Optional[str] = None,
        scenario: str = "general"
    ) -> str:
        """
        构建审核上下文

        Args:
            chunk: 文本块
            external_context: 外部上下文
            scenario: 场景

        Returns:
            完整的上下文信息
        """
        context_parts = []

        # 添加场景信息
        context_parts.append(f"审核场景: {scenario}")

        # 添加章节信息
        if chunk.chapter:
            context_parts.append(f"所属章节: {chunk.chapter}")

        # 添加文本块位置
        context_parts.append(f"文本块编号: {chunk.chunk_id}")

        # 添加外部上下文
        if external_context:
            context_parts.append(f"\n外部上下文信息:\n{external_context}")

        # 如果有前文信息，添加摘要
        if hasattr(chunk, 'metadata') and chunk.metadata:
            if 'previous_summary' in chunk.metadata:
                context_parts.append(f"\n前文摘要:\n{chunk.metadata['previous_summary']}")

        return '\n'.join(context_parts)

    def _generate_default_review_prompt(self) -> str:
        """生成默认审核提示"""
        return """请对以下文本进行全面的审核，检查：
1. 语言文字的规范性
2. 逻辑表达的清晰性
3. 内容的准确性
4. 格式的正确性

请返回JSON格式的审核结果。"""

    async def _review_with_ai(
        self,
        content: str,
        context: str,
        review_prompt: str
    ) -> Dict[str, Any]:
        """
        使用AI模型进行审核

        Args:
            content: 待审核内容
            context: 上下文
            review_prompt: 审核提示

        Returns:
            AI响应
        """
        full_prompt = f"{review_prompt}\n\n{context}\n\n待审核文本:\n{content}"

        messages = [
            {"role": "system", "content": "你是一个专业的文本审核专家，请仔细分析文本并提供详细的审核结果。"},
            {"role": "user", "content": full_prompt}
        ]

        response = await self.maas_client.chat(
            messages=messages,
            temperature=0.3,
            max_tokens=3000
        )

        return response

    def _parse_ai_response(self, response: Dict[str, Any], chunk_id: int) -> Dict[str, Any]:
        """
        解析AI响应

        Args:
            response: AI响应
            chunk_id: 文本块ID

        Returns:
            解析后的结果
        """
        try:
            if 'choices' in response and len(response['choices']) > 0:
                content = response['choices'][0]['message']['content']

                # 尝试解析JSON
                try:
                    parsed = json.loads(content)
                    return parsed
                except json.JSONDecodeError:
                    # 如果不是JSON，尝试提取信息
                    return {
                        'raw_response': content,
                        'issues': self._extract_issues_from_text(content, chunk_id),
                        'overall_score': self._extract_score_from_text(content),
                        'suggestions': self._extract_suggestions_from_text(content),
                        'summary': content[:200] + "..." if len(content) > 200 else content
                    }

            return {
                'error': '无法解析AI响应',
                'raw_response': str(response),
                'issues': [],
                'overall_score': 0
            }

        except Exception as e:
            self.logger.error(f"解析AI响应失败: {e}")
            return {
                'error': str(e),
                'issues': [],
                'overall_score': 0
            }

    def _extract_issues_from_text(self, text: str, chunk_id: int) -> List[Dict[str, Any]]:
        """从文本中提取问题信息"""
        issues = []

        # 简单的问题提取逻辑
        issue_keywords = ['问题', '错误', '不一致', '建议', '修改']
        lines = text.split('\n')

        for line in lines:
            for keyword in issue_keywords:
                if keyword in line:
                    issues.append({
                        'type': 'extracted',
                        'severity': 'medium',
                        'description': line.strip(),
                        'location': f'文本块{chunk_id}',
                        'suggestion': '',
                        'confidence': 0.5
                    })
                    break

        return issues

    def _extract_score_from_text(self, text: str) -> float:
        """从文本中提取评分"""
        import re

        # 查找评分模式
        score_patterns = [
            r'评分[：:]?\s*(\d+)',
            r'得分[：:]?\s*(\d+)',
            r'(\d+)分',
            r'(\d+)/100'
        ]

        for pattern in score_patterns:
            matches = re.findall(pattern, text)
            if matches:
                try:
                    score = float(matches[0])
                    return min(100, max(0, score))
                except ValueError:
                    continue

        return 75.0  # 默认评分

    def _extract_suggestions_from_text(self, text: str) -> List[str]:
        """从文本中提取建议"""
        suggestions = []

        # 简单的建议提取
        suggestion_patterns = ['建议', '推荐', '可以', '应该', '最好']
        lines = text.split('\n')

        for line in lines:
            for pattern in suggestion_patterns:
                if pattern in line and len(line.strip()) > 10:
                    suggestions.append(line.strip())
                    break

        return suggestions[:5]  # 最多返回5条建议

    def set_review_points_manager(self, manager: ReviewPointsManager):
        """设置审核点管理器"""
        self.review_points_manager = manager