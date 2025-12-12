"""
文件处理工具
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from ..models.text_splitter import TextSplitter


class FileHandler:
    """文件处理器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化文件处理器

        Args:
            config: 配置信息
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # 支持的文件格式
        self.supported_formats = config.get('limits', {}).get('supported_formats', [
            'txt', 'docx', 'pdf', 'html', 'md'
        ])

        # 最大文件大小 (MB)
        self.max_file_size = config.get('limits', {}).get('max_file_size', 50)

    def validate_file(self, file_path: str) -> bool:
        """
        验证文件是否符合要求

        Args:
            file_path: 文件路径

        Returns:
            是否有效
        """
        path = Path(file_path)

        # 检查文件是否存在
        if not path.exists():
            self.logger.error(f"文件不存在: {file_path}")
            return False

        # 检查文件大小
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.max_file_size:
            self.logger.error(f"文件过大: {file_size_mb:.2f}MB (最大: {self.max_file_size}MB)")
            return False

        # 检查文件格式
        file_ext = path.suffix.lower().lstrip('.')
        if file_ext not in self.supported_formats:
            self.logger.error(f"不支持的文件格式: {file_ext}")
            return False

        return True

    def load_text_file(self, file_path: str) -> str:
        """
        加载文本文件

        Args:
            file_path: 文件路径

        Returns:
            文件内容
        """
        if not self.validate_file(file_path):
            raise ValueError(f"文件验证失败: {file_path}")

        return TextSplitter.load_file(file_path)

    def ensure_output_dir(self, output_path: str):
        """
        确保输出目录存在

        Args:
            output_path: 输出路径
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        获取文件信息

        Args:
            file_path: 文件路径

        Returns:
            文件信息
        """
        path = Path(file_path)

        if not path.exists():
            return {}

        stat = path.stat()

        return {
            'name': path.name,
            'path': str(path.absolute()),
            'size': stat.st_size,
            'size_mb': stat.st_size / (1024 * 1024),
            'extension': path.suffix.lower(),
            'created_time': stat.st_ctime,
            'modified_time': stat.st_mtime
        }

    def find_files(self, directory: str, pattern: str = "*") -> List[str]:
        """
        查找文件

        Args:
            directory: 目录路径
            pattern: 文件模式

        Returns:
            文件路径列表
        """
        path = Path(directory)
        if not path.exists():
            return []

        files = []
        for file_path in path.glob(pattern):
            if file_path.is_file():
                ext = file_path.suffix.lower().lstrip('.')
                if ext in self.supported_formats:
                    files.append(str(file_path))

        return sorted(files)