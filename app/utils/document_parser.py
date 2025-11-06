"""
PDF文档解析工具
用于解析PDF文档并提取文字、图片和表格内容，支持本地文件路径、网络URL、字节码和文件流输入
按页结构化输出整个PDF的内容，包括文字、图片及其他类型的信息
"""

import io
import os
import urllib.request
import urllib.parse
import urllib.error
from typing import List, Dict, Any, Optional, Tuple, Union, BinaryIO, Iterator
from pathlib import Path
import base64
import gc
import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager, closing
import logging

import fitz  # PyMuPDF
from PIL import Image
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from tabulate import tabulate

# 配置日志
logger = logging.getLogger(__name__)


class DocumentParserError(Exception):
    """文档解析器基础异常类"""
    pass


class InvalidPDFError(DocumentParserError):
    """无效PDF文件异常"""
    pass


class NetworkDownloadError(DocumentParserError):
    """网络下载异常"""
    pass


class ResourceExhaustionError(DocumentParserError):
    """资源耗尽异常"""
    pass


class ImageType(Enum):
    """图片类型枚举"""
    TEXT = "text"
    CHART = "chart"
    PHOTO = "photo"
    LOGO = "logo"
    OTHER = "other"


class ElementType(Enum):
    """PDF元素类型枚举"""
    TEXT = "text"
    IMAGE = "image"
    TABLE = "table"
    ANNOTATION = "annotation"
    VECTOR_GRAPHIC = "vector_graphic"


@dataclass
class ImageInfo:
    """图片信息数据类"""
    page: int
    index: int
    width: int
    height: int
    colorspace: Optional[str]
    base64: str  # 只保留base64数据，移除img_data降低内存占用
    content_type: ImageType  # 重命名type为content_type，表示图片内容类型
    format: str  # 添加图片格式字段，如PNG、JPEG
    size_ratio: float
    bbox: Optional[Tuple[float, float, float, float]] = None  # 边界框 (x0, y0, x1, y1)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'page': self.page,
            'index': self.index,
            'width': self.width,
            'height': self.height,
            'colorspace': self.colorspace,
            'base64': self.base64,
            'content_type': self.content_type.value,
            'format': self.format,
            'size_ratio': self.size_ratio,
            'bbox': self.bbox
        }


@dataclass
class TableInfo:
    """表格信息数据类"""
    page: int
    index: int
    rows: int
    columns: int
    data: List[List[str]]
    markdown: str
    bbox: Optional[Tuple[float, float, float, float]] = None  # 边界框 (x0, y0, x1, y1)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'page': self.page,
            'index': self.index,
            'rows': self.rows,
            'columns': self.columns,
            'data': self.data,
            'markdown': self.markdown,
            'bbox': self.bbox
        }


@dataclass
class TextBlock:
    """文本块数据类"""
    page: int
    index: int
    text: str
    bbox: Optional[Tuple[float, float, float, float]] = None  # 边界框 (x0, y0, x1, y1)
    font_size: Optional[float] = None
    font_name: Optional[str] = None
    is_bold: Optional[bool] = False
    is_italic: Optional[bool] = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'page': self.page,
            'index': self.index,
            'text': self.text,
            'bbox': self.bbox,
            'font_size': self.font_size,
            'font_name': self.font_name,
            'is_bold': self.is_bold,
            'is_italic': self.is_italic
        }


@dataclass
class DocumentMetadata:
    """文档元数据类"""
    title: str = ""
    author: str = ""
    subject: str = ""
    creator: str = ""
    producer: str = ""
    creation_date: Optional[str] = None
    modification_date: Optional[str] = None
    page_count: int = 0
    file_size: Optional[int] = None
    checksum: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'title': self.title,
            'author': self.author,
            'subject': self.subject,
            'creator': self.creator,
            'producer': self.producer,
            'creation_date': self.creation_date,
            'modification_date': self.modification_date,
            'page_count': self.page_count,
            'file_size': self.file_size,
            'checksum': self.checksum
        }


@dataclass
class PageContent:
    """页面内容数据类"""
    page_number: int
    width: float
    height: float
    rotation: int
    text_blocks: List[TextBlock] = field(default_factory=list)
    images: List[ImageInfo] = field(default_factory=list)
    tables: List[TableInfo] = field(default_factory=list)
    raw_text: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'page_number': self.page_number,
            'width': self.width,
            'height': self.height,
            'rotation': self.rotation,
            'text_blocks': [block.to_dict() for block in self.text_blocks],
            'images': [img.to_dict() for img in self.images],
            'tables': [table.to_dict() for table in self.tables],
            'raw_text': self.raw_text
        }


@dataclass
class ParseResult:
    """文档解析结果类"""
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    source_type: Optional[str] = None  # "local", "url", "bytes", "stream"
    metadata: DocumentMetadata = field(default_factory=DocumentMetadata)
    pages: List[PageContent] = field(default_factory=list)
    is_scanned: bool = False
    parse_success: bool = True
    error_message: Optional[str] = None
    processing_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'file_path': self.file_path,
            'file_name': self.file_name,
            'source_type': self.source_type,
            'metadata': self.metadata.to_dict(),
            'pages': [page.to_dict() for page in self.pages],
            'is_scanned': self.is_scanned,
            'parse_success': self.parse_success,
            'error_message': self.error_message,
            'processing_time': self.processing_time
        }


class DocumentParser:
    """文档解析器，支持PDF文档的文字、图片和表格提取，支持多种输入方式"""
    
    def __init__(self, max_memory_mb: int = 512):
        """
        初始化文档解析器
        
        Args:
            max_memory_mb: 最大内存使用限制（MB）
        """
        self.supported_formats = ['.pdf']
        self.max_memory_mb = max_memory_mb
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        
        logger.info("初始化PDF解析器")
    
    def __del__(self):
        """析构函数，清理资源"""
        pass
    
    def cleanup(self):
        """清理资源"""
        # 由于不再使用临时文件，此方法保留为空以确保向后兼容性
        logger.info("清理PDF解析器资源")
    
    def is_supported(self, file_path: str) -> bool:
        """
        检查文件格式是否支持
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否支持该格式
        """
        return Path(file_path).suffix.lower() in self.supported_formats
    
    def parse_document(
        self, 
        file_input: Union[str, bytes, BinaryIO], 
        extract_images: bool = True, 
        extract_tables: bool = True,
        extract_text_blocks: bool = True,
        file_name: Optional[str] = None,
        max_pages: Optional[int] = None
    ) -> ParseResult:
        """
        解析文档，提取文字、图片和表格，按页结构化输出
        
        Args:
            file_input: 文件输入，可以是文件路径、URL、字节数据或文件流
            extract_images: 是否提取图片
            extract_tables: 是否提取表格
            extract_text_blocks: 是否提取文本块（结构化文本）
            file_name: 文件名（当file_input为字节或文件流时使用）
            max_pages: 最大处理页数（None表示处理所有页）
            
        Returns:
            解析结果对象
        """
        import time
        start_time = time.time()
        
        # 初始化结果对象
        result = ParseResult()
        
        try:
            # 处理不同类型的输入
            file_data, source_type = self._process_file_input(file_input, file_name)
            
            # 设置文件信息
            if isinstance(file_data, str):
                # 如果是文件路径
                result.file_path = file_data
                result.file_name = os.path.basename(file_data) if not file_name else file_name
            else:
                # 如果是字节数据
                result.file_path = None
                result.file_name = file_name or "unknown.pdf"
            
            result.source_type = source_type
            
            # 提取元数据
            result.metadata = self.extract_metadata(file_data)
            
            # 按页提取内容
            result.pages = self.extract_pages_content(
                file_data, 
                extract_images, 
                extract_tables, 
                extract_text_blocks,
                max_pages
            )
            
            # 检测是否为扫描文档
            result.is_scanned = self.is_scanned_document(result.pages)
            
            result.parse_success = True
            
        except InvalidPDFError as e:
            result.parse_success = False
            result.error_message = f"PDF文件无效: {str(e)}"
            logger.error(f"PDF文件无效: {str(e)}")
        except NetworkDownloadError as e:
            result.parse_success = False
            result.error_message = f"网络下载失败: {str(e)}"
            logger.error(f"网络下载失败: {str(e)}")
        except ResourceExhaustionError as e:
            result.parse_success = False
            result.error_message = f"资源不足: {str(e)}"
            logger.error(f"资源不足: {str(e)}")
        except Exception as e:
            result.parse_success = False
            result.error_message = str(e)
            logger.error(f"文档解析失败: {str(e)}")
        
        finally:
            # 计算处理时间
            result.processing_time = time.time() - start_time
            
            # # 强制垃圾回收
            # gc.collect()
        
        return result
    
    def _process_file_input(self, file_input: Union[str, bytes, BinaryIO], file_name: Optional[str] = None) -> Tuple[Union[str, bytes], str]:
        """
        处理不同类型的文件输入，返回文件路径或字节数据
        
        Args:
            file_input: 文件输入，可以是文件路径、URL、字节数据或文件流
            file_name: 文件名（当file_input为字节或文件流时使用）
            
        Returns:
            (文件路径或字节数据, 输入类型) 元组
        """
        # 如果是URL
        if isinstance(file_input, str) and self._is_url(file_input):
            pdf_data, url_file_name = self._download_from_url(file_input)
            # 直接返回字节数据，不创建临时文件
            return pdf_data, "url"
        
        # 如果是本地文件路径
        if isinstance(file_input, str) and os.path.exists(file_input):
            # 验证PDF文件
            self._validate_pdf_file(file_input)
            return file_input, "local"
        
        # 如果是字节数据
        if isinstance(file_input, bytes):
            # 检查大小
            if len(file_input) > self.max_memory_bytes:
                raise ResourceExhaustionError(
                    f"输入数据过大: {len(file_input)} bytes > {self.max_memory_bytes} bytes"
                )
            # 验证PDF数据
            self._validate_pdf_bytes(file_input)
            return file_input, "bytes"
        
        # 如果是文件流
        if hasattr(file_input, 'read'):
            # 重置文件指针
            file_input.seek(0)
            # 读取数据到内存，限制大小
            bytes_written = 0
            chunk_size = 64 * 1024  # 64KB chunks
            chunks = []
            while True:
                chunk = file_input.read(chunk_size)
                if not chunk:
                    break
                bytes_written += len(chunk)
                if bytes_written > self.max_memory_bytes:
                    raise ResourceExhaustionError(
                        f"输入数据过大: {bytes_written} bytes > {self.max_memory_bytes} bytes"
                    )
                chunks.append(chunk)
            
            # 验证PDF数据
            pdf_data = b''.join(chunks)
            self._validate_pdf_bytes(pdf_data)
            return pdf_data, "stream"
        
        raise ValueError("不支持的文件输入类型")
    
    def _is_url(self, url: str) -> bool:
        """检查字符串是否为有效的URL"""
        try:
            result = urllib.parse.urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def _validate_pdf_file(self, file_path: str) -> bool:
        """
        验证PDF文件是否有效
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            是否为有效的PDF文件
        """
        try:
            # 检查文件大小
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                raise InvalidPDFError("PDF文件为空")
            
            # 尝试使用PyMuPDF打开文件
            with fitz.open(file_path) as doc:
                page_count = len(doc)
            
            if page_count == 0:
                raise InvalidPDFError("PDF文件没有页面")
                
            return True
        except fitz.FileDataError:
            raise InvalidPDFError("PDF文件已损坏或格式不正确")
        except Exception as e:
            logger.error(f"验证PDF文件失败: {str(e)}")
            raise InvalidPDFError(f"PDF文件验证失败: {str(e)}")
    
    def _download_from_url(self, url: str, max_retries: int = 3, timeout: int = 30) -> Tuple[bytes, str]:
        """
        从URL下载PDF文件到内存，支持重试机制
        
        Args:
            url: PDF文件的URL
            max_retries: 最大重试次数
            timeout: 下载超时时间（秒）
            
        Returns:
            (PDF字节数据, 文件名) 元组
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # 解析URL获取文件名
                parsed_url = urllib.parse.urlparse(url)
                url_path = parsed_url.path
                file_name = os.path.basename(url_path)
                if not file_name or not file_name.lower().endswith('.pdf'):
                    file_name = f"downloaded_{hashlib.md5(url.encode()).hexdigest()}.pdf"
                
                # 下载文件到内存
                req = urllib.request.Request(url)
                req.add_header('User-Agent', 'Mozilla/5.0')  # 添加User-Agent避免被拒绝
                
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    # 检查响应状态
                    if response.status != 200:
                        raise NetworkDownloadError(f"HTTP错误: {response.status}")
                        
                    # 检查内容类型
                    content_type = response.headers.get('Content-Type', '')
                    if 'application/pdf' not in content_type and 'application/octet-stream' not in content_type:
                        logger.warning(f"URL可能不是PDF文件，Content-Type: {content_type}")
                    
                    # 限制下载大小（100MB）
                    content_length = response.headers.get('Content-Length')
                    if content_length and int(content_length) > 100 * 1024 * 1024:
                        raise ResourceExhaustionError("文件过大，超过100MB限制")
                    
                    # 读取所有数据到内存
                    pdf_data = response.read()
                    
                    # 验证下载的数据
                    self._validate_pdf_bytes(pdf_data)
                    
                    return pdf_data, file_name
                    
            except urllib.error.URLError as e:
                last_error = e
                logger.warning(f"下载尝试 {attempt + 1}/{max_retries} 失败: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
            except Exception as e:
                last_error = e
                logger.error(f"下载尝试 {attempt + 1}/{max_retries} 失败: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
        
        raise NetworkDownloadError(f"下载失败，已尝试 {max_retries} 次: {str(last_error)}")
    
    def _validate_pdf_bytes(self, pdf_data: bytes) -> bool:
        """
        验证PDF字节数据是否有效
        
        Args:
            pdf_data: PDF字节数据
            
        Returns:
            是否为有效的PDF数据
        """
        try:
            # 检查数据大小
            if len(pdf_data) == 0:
                raise InvalidPDFError("PDF数据为空")
            
            # 检查PDF文件头
            if not pdf_data.startswith(b'%PDF-'):
                raise InvalidPDFError("数据不是有效的PDF格式")
            
            # 尝试使用PyMuPDF打开数据
            with fitz.open(stream=pdf_data, filetype="pdf") as doc:
                page_count = len(doc)
            
            if page_count == 0:
                raise InvalidPDFError("PDF文件没有页面")
                
            return True
        except fitz.FileDataError:
            raise InvalidPDFError("PDF数据已损坏或格式不正确")
        except Exception as e:
            logger.error(f"验证PDF数据失败: {str(e)}")
            raise InvalidPDFError(f"PDF数据验证失败: {str(e)}")
    
    def _is_supported_input(self, file_input: Union[str, bytes, BinaryIO], file_path: Optional[str] = None, file_name: Optional[str] = None) -> bool:
        """
        检查输入是否为支持的格式
        
        Args:
            file_input: 文件输入
            file_path: 文件路径（如果有）
            file_name: 文件名（如果有）
            
        Returns:
            是否支持该格式
        """
        # 如果是文件路径，检查扩展名
        if isinstance(file_input, str) and not self._is_url(file_input):
            return self.is_supported(file_input)
        
        # 如果是URL，尝试从URL路径获取扩展名
        if isinstance(file_input, str) and self._is_url(file_input):
            parsed_url = urllib.parse.urlparse(file_input)
            url_path = parsed_url.path
            if url_path:
                return Path(url_path).suffix.lower() in self.supported_formats
            return True  # 如果URL没有明确的扩展名，假设是PDF
        
        # 如果是字节数据或文件流，尝试从文件名获取扩展名
        if file_name:
            return Path(file_name).suffix.lower() in self.supported_formats
        
        # 如果没有文件名，默认假设是PDF（因为当前只支持PDF）
        return True
    
    def extract_pages_content(
        self, 
        file_input: Union[str, bytes, fitz.Document], 
        extract_images: bool = True, 
        extract_tables: bool = True,
        extract_text_blocks: bool = True,
        max_pages: Optional[int] = None,
        start_page: Optional[int] = None,
        end_page: Optional[int] = None
    ) -> List[PageContent]:
        """
        按页提取PDF内容
        
        Args:
            file_input: PDF文件路径、字节数据或PyMuPDF文档对象
            extract_images: 是否提取图片
            extract_tables: 是否提取表格
            extract_text_blocks: 是否提取文本块（结构化文本）
            max_pages: 最大处理页数（None表示处理所有页）
            start_page: 起始页（0-based，None表示从第一页开始）
            end_page: 结束页（不包含，None表示到最后一页）
            
        Returns:
            页面内容列表
        """
        pages = []
        
        try:
            # 处理不同类型的输入
            if isinstance(file_input, str):
                # 如果是文件路径，打开文档
                with fitz.open(file_input) as pdf_document:
                    pages = self._extract_pages_from_documents(
                        pdf_document, extract_images, extract_tables, 
                        extract_text_blocks, max_pages, start_page, end_page
                    )
            elif isinstance(file_input, bytes):
                # 如果是字节数据，直接从内存打开
                with fitz.open(stream=file_input, filetype="pdf") as pdf_document:
                    pages = self._extract_pages_from_documents(
                        pdf_document, extract_images, extract_tables, 
                        extract_text_blocks, max_pages, start_page, end_page
                    )
            else:
                # 如果是PyMuPDF文档对象，直接使用
                pdf_document = file_input
                pages = self._extract_pages_from_documents(
                    pdf_document, extract_images, extract_tables, 
                    extract_text_blocks, max_pages, start_page, end_page
                )
            
        except Exception as e:
            raise Exception(f"提取页面内容失败: {str(e)}")
        
        return pages
    
    def _extract_pages_from_documents(
        self,
        pdf_document: fitz.Document,
        extract_images: bool,
        extract_tables: bool,
        extract_text_blocks: bool,
        max_pages: Optional[int] = None,
        start_page: Optional[int] = None,
        end_page: Optional[int] = None
    ) -> List[PageContent]:
        """
        从已打开的文档对象中提取页面内容
        
        Args:
            pdf_document: PyMuPDF文档对象
            extract_images: 是否提取图片
            extract_tables: 是否提取表格
            extract_text_blocks: 是否提取文本块
            max_pages: 最大处理页数
            start_page: 起始页
            end_page: 结束页
            
        Returns:
            页面内容列表
        """
        pages = []
        total_pages = len(pdf_document)
        
        # 确定页面范围
        if start_page is None:
            start_page = 0
        if end_page is None:
            end_page = total_pages
            
        # 应用max_pages限制
        if max_pages is not None and max_pages > 0:
            end_page = min(end_page, start_page + max_pages)
        
        # 确保页面范围有效
        start_page = max(0, start_page)
        end_page = min(total_pages, end_page)
        
        # 提取每一页的内容
        for page_num in range(start_page, end_page):
            page_content = self._process_page(
                pdf_document, page_num, extract_images, 
                extract_tables, extract_text_blocks
            )
            pages.append(page_content)
            
            # 定期进行垃圾回收，控制内存使用
            if page_num % 5 == 0:  # 每5页回收一次
                gc.collect()
                logger.debug(f"已处理第 {page_num + 1} 页，执行垃圾回收")
        
        return pages
    
    def _process_page(
        self, 
        pdf_document: fitz.Document, 
        page_num: int, 
        extract_images: bool, 
        extract_tables: bool, 
        extract_text_blocks: bool
    ) -> PageContent:
        """
        处理单个页面的通用方法
        
        Args:
            pdf_document: PyMuPDF文档对象
            page_num: 页码（0-based）
            extract_images: 是否提取图片
            extract_tables: 是否提取表格
            extract_text_blocks: 是否提取文本块
            
        Returns:
            页面内容对象
        """
        try:
            # 获取页面基本信息
            fitz_page = pdf_document[page_num]
            
            # 创建页面内容对象
            page_content = PageContent(
                page_number=page_num + 1,
                width=fitz_page.rect.width,
                height=fitz_page.rect.height,
                rotation=fitz_page.rotation
            )
            
            # 提取原始文本
            blocks = fitz_page.get_text("blocks") or ""
            # print(blocks)
            for b in sorted(blocks, key=lambda x: (round(x[1]), x[0])):
                page_content.raw_text += b[4].replace('\n', ' ') + "\n"
            # page_content.raw_text = fitz_page.get_text() or ""
            
            # 提取结构化文本块
            if extract_text_blocks:
                page_content.text_blocks = self._extract_text_blocks_fitz(fitz_page, page_num + 1)
            
            # 提取图片
            if extract_images:
                page_content.images = self._extract_page_images(fitz_page, page_num + 1)
                # 立即释放图片内存
                for img in page_content.images:
                    if hasattr(img, 'data') and img.data:
                        img.data = None
            
            # 提取表格
            if extract_tables:
                page_content.tables = self._extract_page_tables_fitz(fitz_page, page_num + 1)
            return page_content
                
        except Exception as e:
            logger.error(f"处理第 {page_num + 1} 页失败: {str(e)}")
            # 创建一个空页面对象，确保页面索引连续
            return PageContent(
                page_number=page_num + 1,
                width=0,
                height=0,
                rotation=0
            )
    
    def _extract_text_blocks(self, page, page_num: int) -> List[TextBlock]:
        """
        从页面提取结构化文本块
        
        Args:
            page: pdfplumber的页面对象
            page_num: 页码
            
        Returns:
            文本块列表
        """
        text_blocks = []
        
        try:
            # 提取字符信息
            chars = page.chars
            
            # 如果没有字符信息，返回空列表
            if not chars:
                return text_blocks
            
            # 按行分组字符
            lines = {}
            for char in chars:
                y0 = round(char['top'], 1)  # 使用四舍五入避免浮点精度问题
                if y0 not in lines:
                    lines[y0] = []
                lines[y0].append(char)
            
            # 对每行按x坐标排序
            for y0 in sorted(lines.keys()):
                line_chars = sorted(lines[y0], key=lambda c: c['x0'])
                
                # 构建文本块
                text = "".join([char['text'] for char in line_chars])
                
                if text.strip():  # 只添加非空文本
                    # 计算边界框
                    x0 = min(char['x0'] for char in line_chars)
                    y0 = min(char['top'] for char in line_chars)
                    x1 = max(char['x1'] for char in line_chars)
                    y1 = max(char['bottom'] for char in line_chars)
                    
                    # 获取字体信息（使用第一个字符的字体信息）
                    font_name = line_chars[0].get('fontname', '')
                    font_size = line_chars[0].get('size', 0)
                    
                    # 检测是否为粗体或斜体
                    is_bold = 'bold' in font_name.lower()
                    is_italic = 'italic' in font_name.lower()
                    
                    text_block = TextBlock(
                        page=page_num,
                        index=len(text_blocks),
                        text=text,
                        bbox=(x0, y0, x1, y1),
                        font_size=font_size,
                        font_name=font_name,
                        is_bold=is_bold,
                        is_italic=is_italic
                    )
                    
                    text_blocks.append(text_block)
            
        except Exception as e:
            logger.error(f"提取文本块失败: {str(e)}")
        
        return text_blocks
    
    def _extract_page_images(self, page, page_num: int) -> List[ImageInfo]:
        """
        从页面提取图片
        
        Args:
            page: PyMuPDF的页面对象
            page_num: 页码
            
        Returns:
            图片信息列表
        """
        images = []
        
        try:
            image_list = page.get_images(full=True)
            
            for img_index, img in enumerate(image_list):
                try:
                    # 获取图片引用
                    xref = img[0]
                    pix = fitz.Pixmap(page.parent, xref)
                    
                    # 跳过CMYK图像
                    if pix.n - pix.alpha < 4:
                        # 将图片转换为字节，然后直接编码为base64
                        img_data = pix.tobytes("png")
                        base64_data = base64.b64encode(img_data).decode('utf-8')
                        
                        # 立即释放图片数据内存
                        img_data = None
                        
                        # 分析图片特征，判断可能是文本还是图片
                        img_type = self._classify_image(pix)
                        
                        # 获取图片位置信息
                        img_rect = page.get_image_bbox(img)
                        
                        # 创建图片信息对象
                        img_info = ImageInfo(
                            page=page_num,
                            index=img_index,
                            width=pix.width,
                            height=pix.height,
                            colorspace=pix.colorspace.name if pix.colorspace else None,
                            base64=base64_data,  # 只保存base64数据
                            content_type=img_type,
                            format="png",  # 假设所有图片都是PNG格式
                            size_ratio=pix.width / pix.height if pix.height > 0 else 0,
                            bbox=(img_rect.x0, img_rect.y0, img_rect.x1, img_rect.y1) if img_rect else None
                        )
                        
                        images.append(img_info)
                    
                    # 释放资源
                    pix = None
                    
                except Exception as e:
                    logger.error(f"提取图片 {img_index} 失败: {str(e)}")
                    continue
            
        except Exception as e:
            logger.error(f"提取页面图片失败: {str(e)}")
        
        return images
    
    def _classify_image(self, pix) -> ImageType:
        """
        根据图片特征分类图片类型
        
        Args:
            pix: PyMuPDF的Pixmap对象
            
        Returns:
            图片类型枚举
        """
        # 基于尺寸和宽高比的简单分类
        width, height = pix.width, pix.height
        size_ratio = width / height if height > 0 else 0
        
        # 文档页面通常的宽高比
        if 0.6 <= size_ratio <= 1.8:
            # 如果图片尺寸接近页面大小，可能是扫描的文本页面
            if width > 400 and height > 500:
                return ImageType.TEXT
            # 中等尺寸可能是图表
            elif width > 200 and height > 200:
                return ImageType.CHART
        
        # 正方形或接近正方形可能是logo或图标
        if 0.8 <= size_ratio <= 1.2:
            return ImageType.LOGO
        
        # 宽高比较大或较小可能是照片
        if size_ratio > 2 or size_ratio < 0.5:
            return ImageType.PHOTO
        
        # 默认为其他类型
        return ImageType.OTHER
    
    def _extract_text_blocks_fitz(self, page, page_num: int) -> List[TextBlock]:
        """
        使用PyMuPDF从页面提取结构化文本块
        
        Args:
            page: PyMuPDF的页面对象
            page_num: 页码
            
        Returns:
            文本块列表
        """
        text_blocks = []
        
        try:
            # 获取页面的文本字典，包含结构化信息
            text_dict = page.get_text("dict")
            
            # 遍历所有文本块
            for block in text_dict.get("blocks", []):
                # 只处理包含文本的块
                if "lines" in block:
                    # 遍历块中的所有行
                    for line in block.get("lines", []):
                        # 遍历行中的所有span
                        for span in line.get("spans", []):
                            text = span.get("text", "")
                            
                            if text.strip():  # 只添加非空文本
                                # 获取边界框
                                bbox = span.get("bbox", (0, 0, 0, 0))
                                
                                # 获取字体信息
                                font_name = span.get("font", "")
                                font_size = span.get("size", 0)
                                
                                # 检测是否为粗体或斜体
                                is_bold = "bold" in font_name.lower()
                                is_italic = "italic" in font_name.lower()
                                
                                # 创建文本块对象
                                text_block = TextBlock(
                                    page=page_num,
                                    index=len(text_blocks),
                                    text=text,
                                    bbox=bbox,
                                    font_size=font_size,
                                    font_name=font_name,
                                    is_bold=is_bold,
                                    is_italic=is_italic
                                )
                                
                                text_blocks.append(text_block)
            
        except Exception as e:
            logger.error(f"使用PyMuPDF提取文本块失败: {str(e)}")
        
        return text_blocks
    
    def _extract_page_tables_fitz(self, page, page_num: int) -> List[TableInfo]:
        """
        使用PyMuPDF从页面提取表格
        
        Args:
            page: PyMuPDF的页面对象
            page_num: 页码
            
        Returns:
            表格信息列表
        """
        tables = []
        
        try:
            # 使用PyMuPDF的find_tables方法检测表格
            table_finder = page.find_tables()
            
            # 获取所有找到的表格
            found_tables = table_finder.tables
            
            for table_index, table in enumerate(found_tables):
                try:
                    # 提取表格数据
                    table_data = table.extract()
                    
                    # 清理表格数据
                    cleaned_table = []
                    for row in table_data:
                        cleaned_row = []
                        for cell in row:
                            # 处理None值
                            cleaned_row.append(cell if cell is not None else "")
                        cleaned_table.append(cleaned_row)
                    
                    # 将表格转换为Markdown格式
                    table_markdown = self._table_to_markdown(cleaned_table)
                    
                    # 获取表格边界框
                    table_bbox = table.bbox
                    
                    # 创建表格信息对象
                    table_info = TableInfo(
                        page=page_num,
                        index=table_index,
                        rows=len(cleaned_table),
                        columns=len(cleaned_table[0]) if cleaned_table else 0,
                        data=cleaned_table,
                        markdown=table_markdown,
                        bbox=table_bbox
                    )
                    
                    tables.append(table_info)
                    
                except Exception as e:
                    logger.error(f"处理表格 {table_index} 失败: {str(e)}")
                    continue
            
        except Exception as e:
            logger.error(f"使用PyMuPDF提取页面表格失败: {str(e)}")
        
        return tables
    
    def _table_to_markdown(self, table: List[List[str]]) -> str:
        """
        将表格数据转换为Markdown格式
        
        Args:
            table: 表格数据
            
        Returns:
            Markdown格式的表格
        """
        if not table:
            return ""
        
        try:
            # 使用tabulate库将表格转换为Markdown
            return tabulate(table, tablefmt="pipe")
        except Exception:
            # 如果tabulate失败，手动转换
            markdown = ""
            
            # 表头
            if table:
                markdown += "| " + " | ".join(table[0]) + " |\n"
                markdown += "| " + " | ".join(["---"] * len(table[0])) + " |\n"
                
                # 表格内容
                for row in table[1:]:
                    markdown += "| " + " | ".join(row) + " |\n"
            
            return markdown
    
    def is_scanned_document(self, pages: List[PageContent]) -> bool:
        """
        检测文档是否主要是扫描版（图片为主）
        
        Args:
            pages: 页面内容列表
            
        Returns:
            是否是扫描版文档
        """
        try:
            if not pages:
                return False
                
            # 计算总文本长度和总图片数量
            total_text_length = sum(len(page.raw_text) for page in pages)
            total_images = sum(len(page.images) for page in pages)
            
            # 如果文本很少且图片较多，可能是扫描版
            avg_text_per_page = total_text_length / len(pages) if pages else 0
            avg_images_per_page = total_images / len(pages) if pages else 0
            
            # 判断标准：每页平均文本少于100字符且每页平均图片数大于0.5
            return avg_text_per_page < 100 and avg_images_per_page > 0.5
            
        except Exception as e:
            logger.error(f"检测扫描文档失败: {str(e)}")
            return False
    
    def extract_metadata(self, file_input: Union[str, bytes]) -> DocumentMetadata:
        """
        提取PDF文档的元数据
        
        Args:
            file_input: PDF文件路径或字节数据
            
        Returns:
            文档元数据对象
        """
        metadata = DocumentMetadata()
        
        try:
            # 处理不同类型的输入
            if isinstance(file_input, str):
                # 如果是文件路径
                file_path = file_input
                # 获取文件大小
                file_size = os.path.getsize(file_path)
                metadata.file_size = file_size
                
                # 计算MD5校验和（仅对小于100MB的文件）
                if file_size < 100 * 1024 * 1024:  # 100MB
                    with open(file_path, 'rb') as f:
                        md5_hash = hashlib.md5()
                        for chunk in iter(lambda: f.read(4096), b""):
                            md5_hash.update(chunk)
                        metadata.checksum = md5_hash.hexdigest()
                
                # 使用pypdf提取元数据
                with open(file_path, 'rb') as file:
                    pdf_reader = PdfReader(file)
                    
                    if pdf_reader.metadata:
                        metadata.title = pdf_reader.metadata.get('/Title', '')
                        metadata.author = pdf_reader.metadata.get('/Author', '')
                        metadata.subject = pdf_reader.metadata.get('/Subject', '')
                        metadata.creator = pdf_reader.metadata.get('/Creator', '')
                        metadata.producer = pdf_reader.metadata.get('/Producer', '')
                        metadata.creation_date = pdf_reader.metadata.get('/CreationDate', '')
                        metadata.modification_date = pdf_reader.metadata.get('/ModDate', '')
                    
                    metadata.page_count = len(pdf_reader.pages)
            else:
                # 如果是字节数据
                pdf_data = file_input
                # 计算文件大小
                metadata.file_size = len(pdf_data)
                
                # 计算MD5校验和（仅对小于100MB的文件）
                if metadata.file_size < 100 * 1024 * 1024:  # 100MB
                    md5_hash = hashlib.md5()
                    md5_hash.update(pdf_data)
                    metadata.checksum = md5_hash.hexdigest()
                
                # 使用PyMuPDF提取元数据
                with fitz.open(stream=pdf_data, filetype="pdf") as pdf_document:
                    if pdf_document.metadata:
                        metadata.title = pdf_document.metadata.get('title', '')
                        metadata.author = pdf_document.metadata.get('author', '')
                        metadata.subject = pdf_document.metadata.get('subject', '')
                        metadata.creator = pdf_document.metadata.get('creator', '')
                        metadata.producer = pdf_document.metadata.get('producer', '')
                        metadata.creation_date = pdf_document.metadata.get('creationDate', '')
                        metadata.modification_date = pdf_document.metadata.get('modDate', '')
                    
                    metadata.page_count = len(pdf_document)
                
        except Exception as e:
            logger.error(f"元数据提取失败: {str(e)}")
        
        return metadata
    
    def extract_metadata_from_bytes(self, pdf_data: bytes) -> DocumentMetadata:
        """
        从PDF字节数据中提取元数据（保留此方法以保持向后兼容性）
        
        Args:
            pdf_data: PDF字节数据
            
        Returns:
            文档元数据对象
        """
        return self.extract_metadata(pdf_data)
    

def parse_large_pdf_streaming(
    file_input: Union[str, bytes, BinaryIO], 
    extract_images: bool = True, 
    extract_tables: bool = True,
    extract_text_blocks: bool = True,
    file_name: Optional[str] = None,
    batch_size: int = 5,
    callback: Optional[callable] = None
) -> Dict[str, Any]:
    """
    流式处理大型PDF文档的便捷函数，分批处理以降低内存占用
    
    Args:
        file_input: 文件输入，可以是文件路径、URL、字节数据或文件流
        extract_images: 是否提取图片
        extract_tables: 是否提取表格
        extract_text_blocks: 是否提取文本块（结构化文本）
        file_name: 文件名（当file_input为字节或文件流时使用）
        batch_size: 每批处理的页数
        callback: 每批处理完成后的回调函数，接收(batch_index, batch_result)参数
        
    Returns:
        包含提取内容的字典
    """
    # 创建自定义解析器实例，限制内存使用
    parser = DocumentParser(max_memory_mb=256)
    
    def _process_batch(pdf_document, batch_start, batch_end):
        """处理单个批次的辅助函数"""
        return parser.extract_pages_content(
            pdf_document, extract_images, extract_tables, extract_text_blocks,
            start_page=batch_start, end_page=batch_end
        )
    
    try:
        # 处理不同类型的输入
        is_url = isinstance(file_input, str) and parser._is_url(file_input)
        file_data = None  # 初始化变量
        
        if is_url:
            # 如果是URL，下载到内存
            pdf_data, url_file_name = parser._download_from_url(file_input)
            file_name = file_name or url_file_name
            source_type = "url"
            file_data = pdf_data  # 设置file_data变量
            
            # 获取总页数
            with fitz.open(stream=pdf_data, filetype="pdf") as pdf_document:
                total_pages = len(pdf_document)
        else:
            # 处理文件路径、字节数据或文件流
            file_data, source_type = parser._process_file_input(file_input, file_name)
            
            # 获取总页数
            if isinstance(file_data, str):
                # 文件路径
                with fitz.open(file_data) as pdf_document:
                    total_pages = len(pdf_document)
            else:
                # 字节数据
                with fitz.open(stream=file_data, filetype="pdf") as pdf_document:
                    total_pages = len(pdf_document)
        
        # 分批处理
        all_pages = []
        for batch_start in range(0, total_pages, batch_size):
            batch_end = min(batch_start + batch_size, total_pages)
            
            # 处理当前批次
            if is_url:
                # URL下载的情况，使用流式处理
                with fitz.open(stream=file_data, filetype="pdf") as pdf_document:
                    batch_pages = _process_batch(pdf_document, batch_start, batch_end)
            else:
                # 文件路径、字节数据或文件流的情况
                if isinstance(file_data, str):
                    # 文件路径
                    with fitz.open(file_data) as pdf_document:
                        batch_pages = _process_batch(pdf_document, batch_start, batch_end)
                else:
                    # 字节数据
                    with fitz.open(stream=file_data, filetype="pdf") as pdf_document:
                        batch_pages = _process_batch(pdf_document, batch_start, batch_end)
            
            all_pages.extend(batch_pages)
            
            # 调用回调函数
            if callback:
                try:
                    callback(batch_start // batch_size, {
                        'pages': batch_pages,
                        'batch_start': batch_start + 1,
                        'batch_end': batch_end,
                        'total_pages': total_pages,
                        'progress': (batch_end / total_pages) * 100
                    })
                except Exception as e:
                    logger.error(f"回调函数执行失败: {str(e)}")
            
            # 强制垃圾回收，释放内存
            gc.collect()
            logger.info(f"已处理批次 {batch_start // batch_size + 1}: 页面 {batch_start + 1}-{batch_end}/{total_pages}")
        
        # 获取元数据
        metadata = parser.extract_metadata(file_data)
        
        # 构建最终结果
        result = {
            'file_path': None if (is_url or not isinstance(file_data, str)) else file_data,
            'file_name': file_name,
            'source_type': source_type,
            'metadata': metadata,
            'pages': all_pages,
            'is_scanned': parser.is_scanned_document(all_pages),
            'parse_success': True,
            'processing_time': 0,  # 这里可以添加计时
            'batch_count': (total_pages + batch_size - 1) // batch_size
        }
        
        return result
        
    except Exception as e:
        logger.error(f"流式处理PDF失败: {str(e)}")
        return {
            'file_path': None,
            'file_name': file_name,
            'source_type': None,
            'metadata': {},
            'pages': [],
            'is_scanned': False,
            'parse_success': False,
            'error_message': str(e),
            'processing_time': 0,
            'batch_count': 0
        }
    finally:
        # 清理资源
        parser.cleanup()


# 创建全局实例
document_parser = DocumentParser()


def parse_pdf_document(
    file_input: Union[str, bytes, BinaryIO], 
    extract_images: bool = True, 
    extract_tables: bool = True,
    extract_text_blocks: bool = True,
    file_name: Optional[str] = None,
    max_pages: Optional[int] = None
) -> Dict[str, Any]:
    """
    解析PDF文档的便捷函数
    
    Args:
        file_input: 文件输入，可以是文件路径、URL、字节数据或文件流
        extract_images: 是否提取图片
        extract_tables: 是否提取表格
        extract_text_blocks: 是否提取文本块（结构化文本）
        file_name: 文件名（当file_input为字节或文件流时使用）
        max_pages: 最大处理页数（None表示处理所有页）
        
    Returns:
        包含提取内容的字典
    """
    result = document_parser.parse_document(
        file_input, extract_images, extract_tables, extract_text_blocks, file_name, max_pages
    )
    return result.to_dict()


def get_pdf_metadata(file_input: Union[str, bytes, BinaryIO]) -> Dict[str, Any]:
    """
    获取PDF元数据的便捷函数
    
    Args:
        file_input: 文件输入，可以是文件路径、URL、字节数据或文件流
        
    Returns:
        文档元数据字典
    """
    return document_parser.extract_metadata(file_input).to_dict()
