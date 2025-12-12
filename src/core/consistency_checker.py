"""
一致性检查器
检查长文本中各部分之间的一致性
"""

import logging
import re
from typing import Dict, Any, List, Optional, Set, Tuple
from collections import defaultdict, Counter
import asyncio

from ..models.text_splitter import TextChunk
from ..models.maas_client import MaaSClient


class ConsistencyChecker:
    """一致性检查器"""

    def __init__(self, maas_client: MaaSClient, config: Dict[str, Any]):
        """
        初始化一致性检查器

        Args:
            maas_client: MAAS客户端
            config: 配置信息
        """
        self.maas_client = maas_client
        self.config = config
        self.logger = logging.getLogger(__name__)

        # 获取一致性检查配置
        review_config = config.get('review', {})
        consistency_config = review_config.get('consistency_check', {})
        self.enable_check = consistency_config.get('enable', True)
        self.check_types = consistency_config.get('check_types', ['terminology', 'facts', 'logic'])
        self.similarity_threshold = consistency_config.get('similarity_threshold', 0.8)

    async def check_consistency(self, chunks: List[TextChunk]) -> Dict[str, Any]:
        """
        执行一致性检查

        Args:
            chunks: 文本块列表

        Returns:
            一致性检查结果
        """
        if not self.enable_check or len(chunks) < 2:
            return {
                'consistency_score': 100,
                'inconsistencies': [],
                'recommendations': [],
                'critical_issues': []
            }

        results = {
            'terminology': await self._check_terminology_consistency(chunks),
            'facts': await self._check_facts_consistency(chunks),
            'logic': await self._check_logic_consistency(chunks)
        }

        # 根据配置选择性检查
        if 'requirements' in self.check_types:
            results['requirements'] = await self._check_requirements_consistency(chunks)

        # 汇总结果
        all_inconsistencies = []
        critical_issues = []
        recommendations = []

        for check_type, result in results.items():
            if check_type in self.check_types:
                all_inconsistencies.extend(result.get('inconsistencies', []))
                critical_issues.extend(result.get('critical_issues', []))
                recommendations.extend(result.get('recommendations', []))

        # 计算整体一致性评分
        consistency_score = self._calculate_consistency_score(results)

        return {
            'consistency_score': consistency_score,
            'inconsistencies': all_inconsistencies,
            'critical_issues': critical_issues,
            'recommendations': recommendations,
            'detailed_results': results
        }

    async def _check_terminology_consistency(self, chunks: List[TextChunk]) -> Dict[str, Any]:
        """检查术语一致性"""
        inconsistencies = []
        recommendations = []

        # 提取各块中的术语
        term_collections = []
        for i, chunk in enumerate(chunks):
            terms = self._extract_terms(chunk.content)
            term_collections.append((i, terms))

        # 检查术语使用一致性
        term_variations = defaultdict(list)
        for chunk_id, terms in term_collections:
            for term in terms:
                normalized = self._normalize_term(term)
                term_variations[normalized].append((chunk_id, term))

        # 发现不一致的术语
        for normalized, occurrences in term_variations.items():
            unique_terms = set(term for _, term in occurrences)
            if len(unique_terms) > 1:
                locations = [f"文本块{chunk_id}" for chunk_id, _ in occurrences]
                inconsistencies.append({
                    'type': 'terminology',
                    'severity': 'medium',
                    'description': f'术语"{normalized}"存在不一致表述: {", ".join(unique_terms)}',
                    'location': ', '.join(locations),
                    'suggestion': f'请统一使用"{max(unique_terms, key=len)}"作为标准表述',
                    'confidence': 0.8
                })

        if inconsistencies:
            recommendations.append("建议创建术语表，确保全文术语使用一致")

        return {
            'inconsistencies': inconsistencies,
            'critical_issues': [],
            'recommendations': recommendations
        }

    async def _check_facts_consistency(self, chunks: List[TextChunk]) -> Dict[str, Any]:
        """检查事实一致性"""
        # 使用AI模型进行事实一致性检查
        inconsistencies = []
        critical_issues = []
        recommendations = []

        try:
            # 构建检查提示
            prompt = self._build_fact_check_prompt(chunks)
            response = await self.maas_client.chat(
                messages=[
                    {"role": "system", "content": "你是一个事实一致性检查专家。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=2000
            )

            # 解析响应
            result = self.maas_client._parse_review_response(response)
            if 'inconsistencies' in result:
                inconsistencies = result['inconsistencies']
            if 'critical_issues' in result:
                critical_issues = result['critical_issues']

        except Exception as e:
            self.logger.error(f"事实一致性检查失败: {e}")

        if inconsistencies:
            recommendations.append("建议核对文中引用的数据和事实的准确性")

        return {
            'inconsistencies': inconsistencies,
            'critical_issues': critical_issues,
            'recommendations': recommendations
        }

    async def _check_logic_consistency(self, chunks: List[TextChunk]) -> Dict[str, Any]:
        """检查逻辑一致性"""
        inconsistencies = []
        recommendations = []

        # 检查相邻文本块之间的逻辑连接
        for i in range(len(chunks) - 1):
            current_chunk = chunks[i]
            next_chunk = chunks[i + 1]

            # 使用AI模型检查逻辑连接
            logic_check = await self._check_logic_between_chunks(current_chunk, next_chunk)
            if logic_check.get('inconsistent'):
                inconsistencies.append({
                    'type': 'logic',
                    'severity': 'medium',
                    'description': logic_check.get('description', '逻辑连接不清晰'),
                    'location': f'文本块{i}与文本块{i+1}之间',
                    'suggestion': logic_check.get('suggestion', '请改善逻辑过渡'),
                    'confidence': logic_check.get('confidence', 0.7)
                })

        if inconsistencies:
            recommendations.append("建议使用过渡词或句子改善文本块之间的逻辑连接")

        return {
            'inconsistencies': inconsistencies,
            'critical_issues': [],
            'recommendations': recommendations
        }

    async def _check_requirements_consistency(self, chunks: List[TextChunk]) -> Dict[str, Any]:
        """检查需求一致性（主要用于合同等场景）"""
        inconsistencies = []
        critical_issues = []
        recommendations = []

        # 提取各块中的需求/要求
        requirements_by_chunk = {}
        for i, chunk in enumerate(chunks):
            requirements = self._extract_requirements(chunk.content)
            if requirements:
                requirements_by_chunk[i] = requirements

        # 检查需求之间的冲突
        requirement_list = []
        for chunk_id, reqs in requirements_by_chunk.items():
            for req in reqs:
                requirement_list.append((chunk_id, req))

        # 使用AI模型检查需求冲突
        if len(requirement_list) > 1:
            conflicts = await self._check_requirement_conflicts(requirement_list)
            inconsistencies.extend(conflicts)

        if inconsistencies:
            critical_issues = [inc for inc in inconsistencies if inc['severity'] == 'critical']
            recommendations.append("建议仔细审查所有需求，确保没有相互冲突的要求")

        return {
            'inconsistencies': inconsistencies,
            'critical_issues': critical_issues,
            'recommendations': recommendations
        }

    def _extract_terms(self, text: str) -> List[str]:
        """提取文本中的术语"""
        # 使用正则表达式和规则提取术语
        terms = []

        # 提取可能的技术术语（通常较长且包含特定字符）
        tech_term_pattern = r'[A-Za-z]{2,}[A-Za-z0-9]*|[一-龥]{2,}[（\(][一-龥A-Za-z0-9]+[）\)]'
        matches = re.findall(tech_term_pattern, text)
        terms.extend(matches)

        # 提取常见的术语模式
        common_patterns = [
            r'[一-龥]{2,}系统',
            r'[一-龥]{2,}技术',
            r'[一-龥]{2,}方法',
            r'[一-龥]{2,]方案',
        ]

        for pattern in common_patterns:
            matches = re.findall(pattern, text)
            terms.extend(matches)

        # 去重并过滤
        unique_terms = list(set(terms))
        return [term for term in unique_terms if len(term) > 2]

    def _normalize_term(self, term: str) -> str:
        """标准化术语用于比较"""
        # 移除标点符号和特殊字符
        normalized = re.sub(r'[^\w\u4e00-\u9fff]', '', term.lower())
        return normalized

    def _extract_requirements(self, text: str) -> List[str]:
        """提取需求/要求"""
        requirements = []

        # 常见的需求标识词
        requirement_patterns = [
            r'应当.*?[。！？]',
            r'必须.*?[。！？]',
            r'需要.*?[。！？]',
            r'要求.*?[。！？]',
            r'规定.*?[。！？]',
        ]

        for pattern in requirement_patterns:
            matches = re.findall(pattern, text)
            requirements.extend(matches)

        return requirements

    def _build_fact_check_prompt(self, chunks: List[TextChunk]) -> str:
        """构建事实检查提示"""
        prompt = "请检查以下文本块之间的事实一致性，特别关注：\n\n"
        prompt += "1. 数据和数字的一致性\n"
        prompt += "2. 日期和时间的一致性\n"
        prompt += "3. 人名、地名、机构名的一致性\n"
        prompt += "4. 事件描述的一致性\n\n"

        for i, chunk in enumerate(chunks):
            prompt += f"\n--- 文本块 {i} ---\n"
            prompt += chunk.content[:1000] + ("..." if len(chunk.content) > 1000 else "")
            prompt += "\n"

        prompt += "\n请返回JSON格式，包含发现的不一致问题。"

        return prompt

    async def _check_logic_between_chunks(self, chunk1: TextChunk, chunk2: TextChunk) -> Dict[str, Any]:
        """检查两个文本块之间的逻辑连接"""
        prompt = f"""请检查以下两个文本块之间的逻辑连接：

文本块1结尾：
{chunk1.content[-500:]}

文本块2开头：
{chunk2.content[:500]}

请判断：
1. 两个部分之间的逻辑连接是否清晰？
2. 是否存在逻辑跳跃或矛盾？
3. 如果需要改进，应该如何改善过渡？

返回JSON格式：
{
    "inconsistent": true/false,
    "description": "问题描述",
    "suggestion": "改进建议",
    "confidence": 0.0-1.0
}
"""

        try:
            response = await self.maas_client.chat(
                messages=[
                    {"role": "system", "content": "你是一个逻辑检查专家。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=500
            )

            result = self.maas_client._parse_review_response(response)
            return result if isinstance(result, dict) else {"inconsistent": False}

        except Exception as e:
            self.logger.error(f"逻辑检查失败: {e}")
            return {"inconsistent": False}

    async def _check_requirement_conflicts(self, requirements: List[Tuple[int, str]]) -> List[Dict[str, Any]]:
        """检查需求冲突"""
        if len(requirements) < 2:
            return []

        # 构建需求检查提示
        prompt = "请检查以下需求是否存在冲突：\n\n"
        for chunk_id, req in requirements:
            prompt += f"[文本块{chunk_id}] {req}\n"

        prompt += "\n请返回JSON格式，列出所有冲突的需求。"

        try:
            response = await self.maas_client.chat(
                messages=[
                    {"role": "system", "content": "你是一个需求分析专家。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1500
            )

            result = self.maas_client._parse_review_response(response)
            if 'inconsistencies' in result:
                return result['inconsistencies']
            return []

        except Exception as e:
            self.logger.error(f"需求冲突检查失败: {e}")
            return []

    def _calculate_consistency_score(self, results: Dict[str, Any]) -> float:
        """计算一致性评分"""
        total_score = 100
        penalty = 0

        for check_type, result in results.items():
            if check_type in self.check_types:
                inconsistencies = result.get('inconsistencies', [])
                critical_issues = result.get('critical_issues', [])

                # 根据问题严重程度扣分
                for issue in critical_issues:
                    penalty += 15 * issue.get('confidence', 1.0)

                for issue in inconsistencies:
                    severity = issue.get('severity', 'medium')
                    if severity == 'critical':
                        penalty += 10 * issue.get('confidence', 1.0)
                    elif severity == 'high':
                        penalty += 5 * issue.get('confidence', 1.0)
                    elif severity == 'medium':
                        penalty += 2 * issue.get('confidence', 1.0)
                    else:
                        penalty += 1 * issue.get('confidence', 1.0)

        return max(0, total_score - penalty)