"""
配置管理器
负责加载和管理所有配置文件
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """配置管理器类"""

    def __init__(self, config_dir: str = "config"):
        """
        初始化配置管理器

        Args:
            config_dir: 配置文件目录路径
        """
        self.config_dir = Path(config_dir)
        self.config = {}
        self.review_points = {}
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """设置日志器"""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def load_config(self, config_file: str = "config.yaml") -> Dict[str, Any]:
        """
        加载主配置文件

        Args:
            config_file: 配置文件名

        Returns:
            配置字典
        """
        config_path = self.config_dir / config_file

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # 处理环境变量替换
            config = self._substitute_env_vars(config)
            self.config = config

            self.logger.info(f"成功加载配置文件: {config_path}")
            return config

        except FileNotFoundError:
            self.logger.error(f"配置文件不存在: {config_path}")
            raise
        except yaml.YAMLError as e:
            self.logger.error(f"配置文件格式错误: {e}")
            raise

    def load_review_points(self, points_file: str = "review_points.yaml") -> Dict[str, Any]:
        """
        加载审核点配置

        Args:
            points_file: 审核点配置文件名

        Returns:
            审核点配置字典
        """
        points_path = self.config_dir / points_file

        try:
            with open(points_path, 'r', encoding='utf-8') as f:
                points = yaml.safe_load(f)

            self.review_points = points

            self.logger.info(f"成功加载审核点配置: {points_path}")
            return points

        except FileNotFoundError:
            self.logger.error(f"审核点配置文件不存在: {points_path}")
            raise
        except yaml.YAMLError as e:
            self.logger.error(f"审核点配置文件格式错误: {e}")
            raise

    def _substitute_env_vars(self, obj: Any) -> Any:
        """
        递归替换配置中的环境变量

        Args:
            obj: 要处理的对象

        Returns:
            处理后的对象
        """
        if isinstance(obj, dict):
            return {k: self._substitute_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._substitute_env_vars(item) for item in obj]
        elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
            env_var = obj[2:-1]
            default_value = None

            # 支持默认值，格式: ${VAR:default_value}
            if ":" in env_var:
                env_var, default_value = env_var.split(":", 1)

            return os.getenv(env_var, default_value)
        else:
            return obj

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值，支持点号分隔的嵌套键

        Args:
            key: 配置键，支持 "section.subsection.key" 格式
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def get_maas_config(self) -> Dict[str, Any]:
        """获取MAAS API配置"""
        return self.get('maas', {})

    def get_text_processing_config(self) -> Dict[str, Any]:
        """获取文本处理配置"""
        return self.get('text_processing', {})

    def get_review_config(self) -> Dict[str, Any]:
        """获取审核配置"""
        return self.get('review', {})

    def get_scenario_config(self, scenario: str) -> Dict[str, Any]:
        """
        获取特定场景的配置

        Args:
            scenario: 场景名称 (contract, media, academic)

        Returns:
            场景配置字典
        """
        scenarios = self.get('scenarios', {})
        return scenarios.get(scenario, {})

    def get_review_points_by_scenario(self, scenario: str) -> Dict[str, Any]:
        """
        根据场景获取相关审核点

        Args:
            scenario: 场景名称

        Returns:
            审核点配置
        """
        if scenario in self.review_points:
            return self.review_points[scenario]
        else:
            return self.review_points.get('general', {})

    def validate_config(self) -> bool:
        """
        验证配置的完整性

        Returns:
            配置是否有效
        """
        required_sections = ['maas', 'text_processing', 'review']

        for section in required_sections:
            if section not in self.config:
                self.logger.error(f"缺少必需的配置节: {section}")
                return False

        maas_config = self.get_maas_config()
        if not maas_config.get('api_key'):
            self.logger.warning("MAAS API密钥未配置，请设置环境变量 MAAS_API_KEY")

        return True

    def get_cache_config(self) -> Dict[str, Any]:
        """获取缓存配置"""
        return self.get('cache', {})

    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return self.get('logging', {})

    def get_limits_config(self) -> Dict[str, Any]:
        """获取限制配置"""
        return self.get('limits', {})


# 全局配置管理器实例
config_manager = ConfigManager()