"""
文本分割器
支持多种分割策略：按章节、段落、语义相似度、固定大小等
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import mimetypes

# 可选依赖
try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    pass  # pdfplumber是可选的

try:
    from bs4 import BeautifulSoup
    HTML_AVAILABLE = True
except ImportError:
    HTML_AVAILABLE = False

@dataclass
class TextChunk:
    """文本块数据类"""
    content: str
    chunk_id: int
    chapter: Optional[str] = None
    section: Optional[str] = None
    start_pos: int = 0
    end_pos: int = 0
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class TextSplitter:
    """文本分割器"""

    # 可用性标志
    PDF_AVAILABLE = PDF_AVAILABLE
    DOCX_AVAILABLE = DOCX_AVAILABLE
    HTML_AVAILABLE = HTML_AVAILABLE

    def __init__(self, config: Dict[str, Any]):
        """
        初始化文本分割器

        Args:
            config: 分割配置
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # 分割策略
        self.strategy = config.get('strategy', 'chapter')
        self.max_chunk_size = config.get('max_chunk_size', 8000)
        self.chunk_overlap = config.get('chunk_overlap', 200)
        self.min_chunk_size = config.get('min_chunk_size', 1000)

        # 章节检测配置
        self.chapter_patterns = config.get('chapter_detection', {}).get('patterns', [])
        self._compile_patterns()

    def _compile_patterns(self):
        """编译章节检测正则表达式"""
        self.compiled_patterns = []
        for pattern in self.chapter_patterns:
            try:
                compiled = re.compile(pattern, re.MULTILINE | re.IGNORECASE)
                self.compiled_patterns.append(compiled)
            except re.error as e:
                self.logger.warning(f"章节模式编译失败: {pattern}, 错误: {e}")

    def split_text(self, text: str, **kwargs) -> List[TextChunk]:
        """
        分割文本

        Args:
            text: 待分割的文本
            **kwargs: 额外参数

        Returns:
            分割后的文本块列表
        """
        if self.strategy == 'chapter':
            return self._split_by_chapter(text)
        elif self.strategy == 'paragraph':
            return self._split_by_paragraph(text)
        elif self.strategy == 'semantic':
            return self._split_by_semantic(text)
        elif self.strategy == 'fixed_size':
            return self._split_by_fixed_size(text)
        else:
            raise ValueError(f"不支持的分割策略: {self.strategy}")

    def _split_by_chapter(self, text: str) -> List[TextChunk]:
        """按章节分割文本"""
        chunks = []

        # 查找所有章节标题
        chapter_matches = []
        for pattern in self.compiled_patterns:
            for match in pattern.finditer(text):
                chapter_matches.append((match.start(), match.end(), match.group()))

        # 按位置排序
        chapter_matches.sort(key=lambda x: x[0])

        # 如果没有找到章节标题，使用固定大小分割
        if not chapter_matches:
            self.logger.warning("未检测到章节标题，使用固定大小分割")
            return self._split_by_fixed_size(text)

        # 创建章节块
        for i, (start, end, title) in enumerate(chapter_matches):
            # 确定章节结束位置
            if i < len(chapter_matches) - 1:
                next_start = chapter_matches[i + 1][0]
                content = text[start:next_start]
            else:
                content = text[start:]

            # 如果块太大，进一步分割
            if len(content) > self.max_chunk_size:
                sub_chunks = self._split_large_content(content, title)
                chunks.extend(sub_chunks)
            else:
                chunk = TextChunk(
                    content=content,
                    chunk_id=i,
                    chapter=title.strip(),
                    start_pos=start,
                    end_pos=start + len(content)
                )
                chunks.append(chunk)

        return chunks

    def _split_by_paragraph(self, text: str) -> List[TextChunk]:
        """按段落分割文本"""
        paragraphs = re.split(r'\n\s*\n', text)
        chunks = []
        current_chunk = ""
        chunk_id = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # 如果添加这个段落会超过最大大小
            if len(current_chunk) + len(para) > self.max_chunk_size and current_chunk:
                chunks.append(TextChunk(
                    content=current_chunk,
                    chunk_id=chunk_id
                ))
                chunk_id += 1
                current_chunk = para
            else:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para

        # 添加最后一个块
        if current_chunk:
            chunks.append(TextChunk(
                content=current_chunk,
                chunk_id=chunk_id
            ))

        return chunks

    def _split_by_fixed_size(self, text: str) -> List[TextChunk]:
        """按固定大小分割文本"""
        chunks = []
        chunk_id = 0

        start = 0
        while start < len(text):
            # 计算结束位置
            end = start + self.max_chunk_size

            # 如果不是最后一块，尝试在句子边界分割
            if end < len(text):
                # 寻找最近的句号、问号、感叹号
                sentence_end = max(
                    text.rfind('。', start, end),
                    text.rfind('？', start, end),
                    text.rfind('！', start, end),
                    text.rfind('.', start, end),
                    text.rfind('?', start, end),
                    text.rfind('!', start, end)
                )

                if sentence_end > start:
                    end = sentence_end + 1
                else:
                    # 如果找不到句子边界，寻找空格
                    space_pos = text.rfind(' ', start, end)
                    if space_pos > start:
                        end = space_pos

            content = text[start:end]
            chunks.append(TextChunk(
                content=content,
                chunk_id=chunk_id,
                start_pos=start,
                end_pos=end
            ))

            chunk_id += 1
            start = end - self.chunk_overlap if end < len(text) else end

        return chunks

    def _split_by_semantic(self, text: str) -> List[TextChunk]:
        """按语义相似度分割文本（简化版本）"""
        # 这里使用段落分割作为基础，然后根据内容长度进一步处理
        paragraphs = self._split_by_paragraph(text)
        chunks = []
        chunk_id = 0
        current_chunk = ""

        for para_chunk in paragraphs:
            if len(current_chunk) + len(para_chunk.content) <= self.max_chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + para_chunk.content
                else:
                    current_chunk = para_chunk.content
            else:
                if current_chunk:
                    chunks.append(TextChunk(
                        content=current_chunk,
                        chunk_id=chunk_id
                    ))
                    chunk_id += 1

                # 如果单个段落太大，直接作为一个块
                if len(para_chunk.content) > self.max_chunk_size:
                    sub_chunks = self._split_large_content(para_chunk.content)
                    chunks.extend(sub_chunks)
                    chunk_id = chunks[-1].chunk_id + 1
                    current_chunk = ""
                else:
                    current_chunk = para_chunk.content

        if current_chunk:
            chunks.append(TextChunk(
                content=current_chunk,
                chunk_id=chunk_id
            ))

        return chunks

    def _split_large_content(self, content: str, chapter: Optional[str] = None) -> List[TextChunk]:
        """分割过大的内容块"""
        chunks = []
        sub_chunk_id = 0

        # 使用固定大小分割
        start = 0
        while start < len(content):
            end = start + self.max_chunk_size

            if end < len(content):
                # 尝试在合适的位置分割
                split_pos = self._find_split_position(content, start, end)
                end = split_pos if split_pos > start else end

            sub_content = content[start:end]
            chunks.append(TextChunk(
                content=sub_content,
                chunk_id=sub_chunk_id,
                chapter=chapter,
                start_pos=start,
                end_pos=end
            ))

            sub_chunk_id += 1
            start = end - self.chunk_overlap if end < len(content) else end

        return chunks

    def _find_split_position(self, text: str, start: int, end: int) -> int:
        """寻找合适的分割位置"""
        # 优先级：句子 > 段落 > 空格
        candidates = []

        # 查找句子结束符
        for char in ['。', '！', '？', '.', '!', '?']:
            pos = text.rfind(char, start, end)
            if pos > start:
                candidates.append(pos + 1)

        # 查找段落分隔
        para_pos = text.rfind('\n\n', start, end)
        if para_pos > start:
            candidates.append(para_pos + 2)

        # 查找空格
        space_pos = text.rfind(' ', start, end)
        if space_pos > start:
            candidates.append(space_pos + 1)

        # 返回最合适的分割位置
        if candidates:
            return max(candidates)
        else:
            return end

    @staticmethod
    def load_file(file_path: str) -> str:
        """
        加载文件内容

        Args:
            file_path: 文件路径

        Returns:
            文件内容
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 根据文件类型处理
        mime_type, _ = mimetypes.guess_type(file_path)

        if mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            return TextSplitter._load_docx(file_path)
        elif mime_type == 'application/pdf':
            return TextSplitter._load_pdf(file_path)
        elif mime_type == 'text/html':
            return TextSplitter._load_html(file_path)
        else:
            # 默认作为纯文本处理
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()

    @staticmethod
    def _load_docx(file_path: str) -> str:
        """加载DOCX文件"""
        if not DOCX_AVAILABLE:
            raise ImportError("需要安装python-docx库来处理DOCX文件")

        doc = docx.Document(file_path)
        content = []

        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                content.append(paragraph.text)

        return '\n\n'.join(content)

    @staticmethod
    def _load_pdf(file_path: str) -> str:
        """加载PDF文件"""
        if not PDF_AVAILABLE:
            raise ImportError("需要安装PyPDF2或pdfplumber库来处理PDF文件")

        try:
            # 优先使用pdfplumber（更好的文本提取）
            with pdfplumber.open(file_path) as pdf:
                content = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        content.append(text)
                return '\n\n'.join(content)
        except:
            # 回退到PyPDF2
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                content = []
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text:
                        content.append(text)
                return '\n\n'.join(content)

    @staticmethod
    def _load_html(file_path: str) -> str:
        """加载HTML文件"""
        if not HTML_AVAILABLE:
            raise ImportError("需要安装beautifulsoup4库来处理HTML文件")

        with open(file_path, 'r', encoding='utf-8') as f:
            html = f.read()

        soup = BeautifulSoup(html, 'html.parser')

        # 提取文本内容，保持段落结构
        content = []
        for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = tag.get_text().strip()
            if text:
                content.append(text)

        return '\n\n'.join(content)

    def get_statistics(self, chunks: List[TextChunk]) -> Dict[str, Any]:
        """
        获取分割统计信息

        Args:
            chunks: 文本块列表

        Returns:
            统计信息
        """
        if not chunks:
            return {}

        sizes = [len(chunk.content) for chunk in chunks]

        return {
            'total_chunks': len(chunks),
            'total_chars': sum(sizes),
            'avg_chunk_size': sum(sizes) / len(sizes),
            'min_chunk_size': min(sizes),
            'max_chunk_size': max(sizes),
            'strategy': self.strategy
        }