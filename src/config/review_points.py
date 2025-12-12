"""
审核点管理系统
负责管理和执行各种审核点
"""

import logging
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from enum import Enum


class CheckType(Enum):
    """审核点类型枚举"""
    FORMAT = "format"
    LANGUAGE = "language"
    CONSISTENCY = "consistency"
    LOGIC = "logic"
    COMPLETENESS = "completeness"
    CONFLICT = "conflict"
    ACCURACY = "accuracy"
    SOURCE = "source"
    BIAS = "bias"
    SENSITIVITY = "sensitivity"
    CLARITY = "clarity"
    INTEGRITY = "integrity"
    FAIRNESS = "fairness"
    FEASIBILITY = "feasibility"


class Priority(Enum):
    """优先级枚举"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CheckScope(Enum):
    """检查范围枚举"""
    LOCAL = "local"      # 单块内检查
    GLOBAL = "global"    # 全局检查
    CROSS = "cross"      # 跨块检查


@dataclass
class ReviewPoint:
    """审核点数据类"""
    name: str
    description: str
    type: CheckType
    priority: Priority
    enabled: bool
    check_scope: CheckScope = CheckScope.LOCAL
    required_items: Optional[List[str]] = None
    check_fields: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ReviewIssue:
    """审核问题数据类"""
    chunk_id: int
    review_point: str
    type: str
    severity: str
    description: str
    location: str
    suggestion: str
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'chunk_id': self.chunk_id,
            'review_point': self.review_point,
            'type': self.type,
            'severity': self.severity,
            'description': self.description,
            'location': self.location,
            'suggestion': self.suggestion,
            'confidence': self.confidence
        }


class ReviewPointsManager:
    """审核点管理器"""

    def __init__(self, review_points_config: Dict[str, Any]):
        """
        初始化审核点管理器

        Args:
            review_points_config: 审核点配置
        """
        self.config = review_points_config
        self.logger = logging.getLogger(__name__)
        self.review_points: Dict[str, ReviewPoint] = {}
        self.scenario_points: Dict[str, List[ReviewPoint]] = {}

        self._load_review_points()

    def _load_review_points(self):
        """加载审核点配置"""
        # 加载通用审核点
        if 'general' in self.config:
            self._load_section_points('general')

        # 加载各场景专用审核点
        for scenario in ['contract', 'media', 'academic']:
            if scenario in self.config:
                self._load_section_points(scenario)

    def _load_section_points(self, section: str):
        """加载特定节的审核点"""
        if section not in self.config:
            return

        section_config = self.config[section]
        self.scenario_points[section] = []

        for category, points in section_config.items():
            for point_config in points:
                review_point = self._create_review_point(point_config)
                self.review_points[review_point.name] = review_point
                self.scenario_points[section].append(review_point)

                self.logger.debug(f"加载审核点: {review_point.name} (场景: {section})")

    def _create_review_point(self, config: Dict[str, Any]) -> ReviewPoint:
        """创建审核点对象"""
        # 解析检查类型
        type_str = config.get('type', 'format')
        check_type = CheckType(type_str) if type_str in [e.value for e in CheckType] else CheckType.FORMAT

        # 解析优先级
        priority_str = config.get('priority', 'medium')
        priority = Priority(priority_str) if priority_str in [e.value for e in Priority] else Priority.MEDIUM

        # 解析检查范围
        scope_str = config.get('check_scope', 'local')
        check_scope = CheckScope(scope_str) if scope_str in [e.value for e in CheckScope] else CheckScope.LOCAL

        return ReviewPoint(
            name=config['name'],
            description=config['description'],
            type=check_type,
            priority=priority,
            enabled=config.get('enabled', True),
            check_scope=check_scope,
            required_items=config.get('required_items'),
            check_fields=config.get('check_fields'),
            metadata=config.get('metadata', {})
        )

    def get_review_points_by_scenario(self, scenario: str) -> List[ReviewPoint]:
        """
        根据场景获取审核点

        Args:
            scenario: 场景名称

        Returns:
            审核点列表
        """
        # 获取场景专用审核点
        scenario_points = self.scenario_points.get(scenario, [])

        # 获取通用审核点
        general_points = self.scenario_points.get('general', [])

        # 合并并去重
        all_points = scenario_points + [p for p in general_points if p not in scenario_points]

        # 过滤启用的审核点
        enabled_points = [p for p in all_points if p.enabled]

        return sorted(enabled_points, key=lambda x: self._priority_value(x.priority))

    def get_global_check_points(self, scenario: str) -> List[ReviewPoint]:
        """
        获取需要全局检查的审核点

        Args:
            scenario: 场景名称

        Returns:
            全局检查点列表
        """
        points = self.get_review_points_by_scenario(scenario)
        return [p for p in points if p.check_scope in [CheckScope.GLOBAL, CheckScope.CROSS]]

    def get_local_check_points(self, scenario: str) -> List[ReviewPoint]:
        """
        获取局部检查点

        Args:
            scenario: 场景名称

        Returns:
            局部检查点列表
        """
        points = self.get_review_points_by_scenario(scenario)
        return [p for p in points if p.check_scope == CheckScope.LOCAL]

    def get_cross_check_points(self, scenario: str) -> List[ReviewPoint]:
        """
        获取跨块检查点

        Args:
            scenario: 场景名称

        Returns:
            跨块检查点列表
        """
        points = self.get_review_points_by_scenario(scenario)
        return [p for p in points if p.check_scope == CheckScope.CROSS]

    def get_review_point_by_name(self, name: str) -> Optional[ReviewPoint]:
        """
        根据名称获取审核点

        Args:
            name: 审核点名称

        Returns:
            审核点对象
        """
        return self.review_points.get(name)

    def get_points_by_type(self, check_type: CheckType) -> List[ReviewPoint]:
        """
        根据类型获取审核点

        Args:
            check_type: 检查类型

        Returns:
            审核点列表
        """
        return [p for p in self.review_points.values() if p.type == check_type and p.enabled]

    def get_points_by_priority(self, priority: Priority) -> List[ReviewPoint]:
        """
        根据优先级获取审核点

        Args:
            priority: 优先级

        Returns:
            审核点列表
        """
        return [p for p in self.review_points.values() if p.priority == priority and p.enabled]

    def enable_review_point(self, name: str):
        """启用审核点"""
        if name in self.review_points:
            self.review_points[name].enabled = True
            self.logger.info(f"启用审核点: {name}")

    def disable_review_point(self, name: str):
        """禁用审核点"""
        if name in self.review_points:
            self.review_points[name].enabled = False
            self.logger.info(f"禁用审核点: {name}")

    def get_required_checks_for_scenario(self, scenario: str) -> List[str]:
        """
        获取场景必需的检查项

        Args:
            scenario: 场景名称

        Returns:
            必需检查项列表
        """
        # 从配置中获取场景必需检查
        scenario_config = self.config.get('review_point_settings', {}).get('strategies', {})

        required_checks = []

        # 根据场景添加特定的必需检查
        if scenario == 'contract':
            required_checks.extend(['法律条款完整性', '主体信息一致性', '条款冲突'])
        elif scenario == 'media':
            required_checks.extend(['事实准确性', '偏见检测', '敏感内容'])
        elif scenario == 'academic':
            required_checks.extend(['结构完整性', '引用一致性', '方法描述清晰度'])

        return required_checks

    def generate_review_prompt(self, points: List[ReviewPoint]) -> str:
        """
        生成审核提示词

        Args:
            points: 审核点列表

        Returns:
            审核提示词
        """
        prompt_parts = []

        # 添加说明
        prompt_parts.append("请按照以下审核要点对文本进行详细检查：\n")

        # 按优先级分组
        critical_points = [p for p in points if p.priority == Priority.CRITICAL]
        high_points = [p for p in points if p.priority == Priority.HIGH]
        medium_points = [p for p in points if p.priority == Priority.MEDIUM]
        low_points = [p for p in points if p.priority == Priority.LOW]

        # 生成各优先级的审核点
        for priority, points_list in [
            (Priority.CRITICAL, critical_points),
            (Priority.HIGH, high_points),
            (Priority.MEDIUM, medium_points),
            (Priority.LOW, low_points)
        ]:
            if points_list:
                prompt_parts.append(f"\n【{priority.value.upper()}优先级审核点】")
                for point in points_list:
                    prompt_parts.append(f"- {point.name}: {point.description}")
                    if point.required_items:
                        prompt_parts.append(f"  必需项: {', '.join(point.required_items)}")

        # 添加输出格式要求
        prompt_parts.append("\n\n请返回JSON格式的审核结果，包含以下字段：")
        prompt_parts.append("1. overall_score: 整体评分 (0-100)")
        prompt_parts.append("2. issues: 发现的问题列表，每个问题包含：")
        prompt_parts.append("   - type: 问题类型")
        prompt_parts.append("   - severity: 严重程度 (critical/high/medium/low)")
        prompt_parts.append("   - description: 问题描述")
        prompt_parts.append("   - location: 位置信息")
        prompt_parts.append("   - suggestion: 修改建议")
        prompt_parts.append("3. suggestions: 改进建议")
        prompt_parts.append("4. summary: 审核总结")

        return '\n'.join(prompt_parts)

    def _priority_value(self, priority: Priority) -> int:
        """获取优先级数值（用于排序）"""
        priority_order = {
            Priority.CRITICAL: 0,
            Priority.HIGH: 1,
            Priority.MEDIUM: 2,
            Priority.LOW: 3
        }
        return priority_order.get(priority, 3)

    def get_statistics(self) -> Dict[str, Any]:
        """获取审核点统计信息"""
        total_points = len(self.review_points)
        enabled_points = len([p for p in self.review_points.values() if p.enabled])

        # 按类型统计
        type_stats = {}
        for check_type in CheckType:
            count = len([p for p in self.review_points.values() if p.type == check_type])
            if count > 0:
                type_stats[check_type.value] = count

        # 按优先级统计
        priority_stats = {}
        for priority in Priority:
            count = len([p for p in self.review_points.values() if p.priority == priority])
            if count > 0:
                priority_stats[priority.value] = count

        return {
            'total_points': total_points,
            'enabled_points': enabled_points,
            'disabled_points': total_points - enabled_points,
            'by_type': type_stats,
            'by_priority': priority_stats,
            'scenarios': list(self.scenario_points.keys())
        }