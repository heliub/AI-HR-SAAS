"""
PDF转图片工具
用于将PDF文档转换为图片格式，支持自定义输出格式、DPI和图片质量
优化版本：改进资源管理、异常处理、性能和代码质量

注意：返回的ImageList对象支持上下文管理器，推荐使用with语句自动管理资源。
"""

import os
import tempfile
import asyncio
from io import BytesIO
from typing import List, Optional, Union, BinaryIO, Tuple, Iterator, Dict, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager

from PIL import Image
from pdf2image import convert_from_bytes, convert_from_path, pdfinfo_from_path
import structlog

logger = structlog.get_logger(__name__)


# 自定义异常类
class PDFConversionError(Exception):
    """PDF转换基础异常"""
    pass


class PDFNotFoundError(PDFConversionError):
    """PDF文件未找到异常"""
    pass


class PDFInvalidError(PDFConversionError):
    """PDF文件无效异常"""
    pass


class PDFConversionMemoryError(PDFConversionError):
    """PDF转换内存不足异常"""
    pass


class PDFDependencyError(PDFConversionError):
    """PDF转换依赖缺失异常"""
    pass


@dataclass
class PDFConversionConfig:
    """PDF转换配置"""
    DEFAULT_DPI: int = 200
    DEFAULT_FORMAT: str = "PNG"
    DEFAULT_QUALITY: int = 85
    SUPPORTED_FORMATS: List[str] = None
    
    def __post_init__(self):
        if self.SUPPORTED_FORMATS is None:
            self.SUPPORTED_FORMATS = ["PNG", "JPEG", "WEBP"]
        
        if self.output_format not in self.SUPPORTED_FORMATS:
            raise ValueError(f"不支持的输出格式: {self.output_format}，支持的格式: {', '.join(self.SUPPORTED_FORMATS)}")
        
        if not 1 <= self.quality <= 100:
            raise ValueError(f"图片质量必须在1-100之间，当前值: {self.quality}")
    
    dpi: int = DEFAULT_DPI
    output_format: str = DEFAULT_FORMAT
    quality: int = DEFAULT_QUALITY
    thread_count: int = 1
    batch_size: int = 5
    max_workers: int = 4


class ImageList:
    """图片列表上下文管理器，用于自动管理图片资源"""
    
    def __init__(self, images: List[Image.Image]):
        """
        初始化图片列表上下文管理器
        
        Args:
            images: PIL Image对象列表
        """
        self.images = images
        self._closed = False
    
    def __enter__(self) -> List[Image.Image]:
        """
        进入上下文管理器
        
        Returns:
            PIL Image对象列表
        """
        return self.images
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        退出上下文管理器，自动关闭所有图片
        
        Args:
            exc_type: 异常类型
            exc_val: 异常值
            exc_tb: 异常跟踪
        """
        self.close()
        return False  # 不抑制异常
    
    def close(self):
        """关闭所有图片对象"""
        if not self._closed:
            for img in self.images:
                if hasattr(img, 'close'):
                    img.close()
            self._closed = True
    
    def __del__(self):
        """析构函数，确保资源被释放"""
        self.close()


class PDFToImageConverter:
    """PDF转图片转换器"""
    
    def __init__(self, config: Optional[PDFConversionConfig] = None):
        """
        初始化PDF转图片转换器
        
        Args:
            config: PDF转换配置，如果为None则使用默认配置
        """
        self.config = config or PDFConversionConfig()
        
        # 检查依赖
        self._check_dependencies()
    
    def _check_dependencies(self) -> None:
        """检查必要的依赖是否安装"""
        try:
            # 尝试导入pdf2image
            import pdf2image
            
            # 检查poppler是否安装
            # 使用一个不存在的文件路径来测试poppler是否可用
            # 这会抛出异常但能验证poppler是否安装
            try:
                pdfinfo_from_path("/nonexistent_file_for_testing.pdf")
            except (FileNotFoundError, OSError) as e:
                # 预期的异常，说明poppler可用
                pass
            except Exception as e:
                # 其他异常可能表示poppler未安装
                if "poppler" in str(e).lower():
                    raise PDFDependencyError(
                        "pdf2image的依赖poppler未正确安装。"
                        "请参考 https://github.com/Belval/pdf2image 安装说明。"
                    ) from e
        except ImportError as e:
            raise PDFDependencyError(
                "pdf2image库未安装。请使用 'pip install pdf2image' 安装。"
            ) from e
    
    def _is_valid_pdf(self, pdf_path: str) -> bool:
        """
        验证PDF文件是否有效
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            是否为有效的PDF文件
        """
        try:
            # 尝试获取PDF信息
            pdfinfo_from_path(pdf_path)
            return True
        except Exception:
            return False
    
    def _validate_page_range(
        self,
        first_page: Optional[int],
        last_page: Optional[int],
        total_pages: int
    ) -> Tuple[int, int]:
        """
        验证并标准化页码范围
        
        Args:
            first_page: 起始页码
            last_page: 结束页码
            total_pages: 总页数
            
        Returns:
            标准化后的(起始页码, 结束页码)
        """
        first_page = first_page or 1
        last_page = last_page or total_pages
        
        if first_page < 1:
            raise ValueError(f"起始页码必须大于0，当前值: {first_page}")
        
        if last_page > total_pages:
            raise ValueError(f"结束页码不能超过总页数({total_pages})，当前值: {last_page}")
        
        if first_page > last_page:
            raise ValueError(f"起始页码({first_page})不能大于结束页码({last_page})")
        
        return first_page, last_page
    
    @contextmanager
    def _managed_images(self, images: List[Image.Image]):
        """
        上下文管理器，确保图片资源被正确释放
        
        Args:
            images: PIL Image对象列表
        """
        try:
            yield images
        finally:
            # 确保所有图片对象被关闭
            for img in images:
                if hasattr(img, 'close'):
                    img.close()
    
    def _images_to_bytes(self, images: List[Image.Image]) -> List[bytes]:
        """
        将PIL Image对象列表转换为字节数据列表
        
        Args:
            images: PIL Image对象列表
            
        Returns:
            图片字节数据列表
        """
        image_bytes_list = []
        for img in images:
            buffer = BytesIO()
            try:
                # 根据输出格式设置保存参数
                save_kwargs = {"format": self.config.output_format}
                if self.config.output_format in ["JPEG", "JPG"]:
                    save_kwargs["quality"] = self.config.quality
                    # JPEG不支持透明度，需要转换为RGB
                    if img.mode in ("RGBA", "LA", "P"):
                        img = img.convert("RGB")
                
                img.save(buffer, **save_kwargs)
                image_bytes_list.append(buffer.getvalue())
            finally:
                buffer.close()
        
        return image_bytes_list
    
    def _convert_pdf_common(
        self,
        pdf_path: Optional[str] = None,
        pdf_bytes: Optional[bytes] = None,
        first_page: Optional[int] = None,
        last_page: Optional[int] = None
    ) -> List[Image.Image]:
        """
        PDF转换的通用逻辑
        
        Args:
            pdf_path: PDF文件路径
            pdf_bytes: PDF文件字节数据
            first_page: 起始页码
            last_page: 结束页码
            
        Returns:
            PIL Image对象列表
        """
        if pdf_path is None and pdf_bytes is None:
            raise ValueError("必须提供pdf_path或pdf_bytes中的一个")
        
        if pdf_path is not None:
            if not os.path.exists(pdf_path):
                raise PDFNotFoundError(f"PDF文件不存在: {pdf_path}")
            
            if not self._is_valid_pdf(pdf_path):
                raise PDFInvalidError(f"PDF文件无效或损坏: {pdf_path}")
            
            # 获取PDF信息
            try:
                pdf_info = pdfinfo_from_path(pdf_path)
                total_pages = pdf_info["Pages"]
            except Exception as e:
                raise PDFInvalidError(f"无法读取PDF信息: {str(e)}") from e
        else:
            if not pdf_bytes:
                raise ValueError("PDF字节数据不能为空")
            
            # 对于字节数据，我们无法预先获取页数，将在转换后处理
            total_pages = None
        
        # 验证页码范围
        if total_pages:
            first_page, last_page = self._validate_page_range(first_page, last_page, total_pages)
        
        try:
            # 准备转换参数
            kwargs = {
                "dpi": self.config.dpi,
                "fmt": self.config.output_format,
                "thread_count": self.config.thread_count
            }
            
            if first_page is not None:
                kwargs["first_page"] = first_page
            
            if last_page is not None:
                kwargs["last_page"] = last_page
            
            # 执行转换
            if pdf_path is not None:
                images = convert_from_path(pdf_path, **kwargs)
            else:
                images = convert_from_bytes(pdf_bytes, **kwargs)
            
            return images
            
        except MemoryError:
            raise PDFConversionMemoryError(
                f"内存不足，无法转换PDF。请尝试减少DPI或分批处理。"
            )
        except Exception as e:
            logger.error(
                "PDF转图片失败",
                pdf_path=pdf_path,
                pdf_bytes_size=len(pdf_bytes) if pdf_bytes else None,
                error=str(e)
            )
            raise PDFConversionError(f"PDF转图片失败: {str(e)}") from e
    
    def convert_from_path(
        self,
        pdf_path: str,
        first_page: Optional[int] = None,
        last_page: Optional[int] = None
    ) -> ImageList:
        """
        从PDF文件路径转换为图片
        
        Args:
            pdf_path: PDF文件路径
            first_page: 起始页码(从1开始)
            last_page: 结束页码(从1开始)
            
        Returns:
            ImageList对象，支持上下文管理器自动释放资源
        """
        # 直接获取图片，不使用上下文管理器
        # 让ImageList管理资源
        images = self._convert_pdf_common(
            pdf_path=pdf_path,
            first_page=first_page,
            last_page=last_page
        )
        
        # 返回ImageList对象，支持自动资源管理
        return ImageList(images)
    
    def convert_from_bytes(
        self,
        pdf_bytes: bytes,
        first_page: Optional[int] = None,
        last_page: Optional[int] = None
    ) -> ImageList:
        """
        从PDF字节数据转换为图片
        
        Args:
            pdf_bytes: PDF文件字节数据
            first_page: 起始页码(从1开始)
            last_page: 结束页码(从1开始)
            
        Returns:
            ImageList对象，支持上下文管理器自动释放资源
        """
        # 直接获取图片，不使用上下文管理器
        # 让ImageList管理资源
        images = self._convert_pdf_common(
            pdf_bytes=pdf_bytes,
            first_page=first_page,
            last_page=last_page
        )
        
        # 返回ImageList对象，支持自动资源管理
        return ImageList(images)
    
    def convert_to_bytes(
        self,
        pdf_path: str,
        first_page: Optional[int] = None,
        last_page: Optional[int] = None
    ) -> List[bytes]:
        """
        从PDF文件路径转换为图片字节数据
        
        Args:
            pdf_path: PDF文件路径
            first_page: 起始页码(从1开始)
            last_page: 结束页码(从1开始)
            
        Returns:
            图片字节数据列表
        """
        # 获取ImageList对象
        image_list = self.convert_from_path(
            pdf_path,
            first_page=first_page,
            last_page=last_page
        )
        
        try:
            # 转换为字节数据
            return self._images_to_bytes(image_list.images)
        finally:
            # 确保图片对象被关闭
            image_list.close()
    
    def convert_to_base64(
        self,
        pdf_path: str,
        first_page: Optional[int] = None,
        last_page: Optional[int] = None
    ) -> List[str]:
        """
        从PDF文件路径转换为Base64编码的图片数据
        
        Args:
            pdf_path: PDF文件路径
            first_page: 起始页码(从1开始)
            last_page: 结束页码(从1开始)
            
        Returns:
            Base64编码的图片数据列表
        """
        import base64
        
        image_bytes_list = self.convert_to_bytes(
            pdf_path,
            first_page=first_page,
            last_page=last_page
        )
        
        # 转换为Base64编码
        base64_list = []
        for img_bytes in image_bytes_list:
            base64_str = base64.b64encode(img_bytes).decode('utf-8')
            base64_list.append(base64_str)
        
        return base64_list
    
    def convert_to_bytes_streaming(
        self,
        pdf_path: str,
        batch_size: Optional[int] = None,
        first_page: Optional[int] = None,
        last_page: Optional[int] = None
    ) -> Iterator[List[bytes]]:
        """
        分批流式转换PDF为图片字节数据，减少内存使用
        
        Args:
            pdf_path: PDF文件路径
            batch_size: 每批处理的页数，默认使用配置中的值
            first_page: 起始页码(从1开始)
            last_page: 结束页码(从1开始)
            
        Yields:
            图片字节数据列表的迭代器
        """
        batch_size = batch_size or self.config.batch_size
        
        # 获取总页数
        pdf_info = self.get_pdf_info(pdf_path)
        total_pages = pdf_info["page_count"]
        
        first_page = first_page or 1
        last_page = last_page or total_pages
        
        # 分批处理
        for start in range(first_page, last_page + 1, batch_size):
            end = min(start + batch_size - 1, last_page)
            batch_bytes = self.convert_to_bytes(pdf_path, start, end)
            yield batch_bytes
    
    
    def get_pdf_info(self, pdf_path: str) -> Dict[str, Any]:
        """
        获取PDF文件信息
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            包含PDF信息的字典
        """
        if not os.path.exists(pdf_path):
            raise PDFNotFoundError(f"PDF文件不存在: {pdf_path}")
        
        try:
            # 获取PDF信息
            pdf_info = pdfinfo_from_path(pdf_path)
            page_count = pdf_info["Pages"]
            
            # 转换第一页以获取尺寸信息
            first_page_images = self.convert_from_path(pdf_path, first_page=1, last_page=1)
            if not first_page_images.images:
                raise PDFInvalidError("无法读取PDF文件")
            
            try:
                first_page = first_page_images.images[0]
                width, height = first_page.size
                
                return {
                    "page_count": page_count,
                    "first_page_size": (width, height),
                    "file_size": os.path.getsize(pdf_path),
                    "output_format": self.config.output_format,
                    "dpi": self.config.dpi
                }
            finally:
                # 确保图片对象被关闭
                first_page_images.close()
            
        except Exception as e:
            logger.error("获取PDF信息失败", pdf_path=pdf_path, error=str(e))
            raise PDFConversionError(f"获取PDF信息失败: {str(e)}") from e
    
    def get_pdf_page_count(self, pdf_path: str) -> int:
        """
        获取PDF文件页数的便捷方法
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            PDF文件页数
        """
        info = self.get_pdf_info(pdf_path)
        return info["page_count"]


class AsyncPDFToImageConverter(PDFToImageConverter):
    """异步PDF转图片转换器"""
    
    def __init__(self, config: Optional[PDFConversionConfig] = None):
        """
        初始化异步PDF转图片转换器
        
        Args:
            config: PDF转换配置，如果为None则使用默认配置
        """
        super().__init__(config)
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_workers)
    
    async def convert_from_path_async(
        self,
        pdf_path: str,
        first_page: Optional[int] = None,
        last_page: Optional[int] = None
    ) -> List[Image.Image]:
        """
        异步转换PDF文件路径为图片
        
        Args:
            pdf_path: PDF文件路径
            first_page: 起始页码(从1开始)
            last_page: 结束页码(从1开始)
            
        Returns:
            PIL Image对象列表
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self.convert_from_path,
            pdf_path,
            first_page,
            last_page
        )
    
    async def convert_from_bytes_async(
        self,
        pdf_bytes: bytes,
        first_page: Optional[int] = None,
        last_page: Optional[int] = None
    ) -> List[Image.Image]:
        """
        异步转换PDF字节数据为图片
        
        Args:
            pdf_bytes: PDF文件字节数据
            first_page: 起始页码(从1开始)
            last_page: 结束页码(从1开始)
            
        Returns:
            PIL Image对象列表
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self.convert_from_bytes,
            pdf_bytes,
            first_page,
            last_page
        )
    
    async def convert_to_bytes_async(
        self,
        pdf_path: str,
        first_page: Optional[int] = None,
        last_page: Optional[int] = None
    ) -> List[bytes]:
        """
        异步转换PDF文件路径为图片字节数据
        
        Args:
            pdf_path: PDF文件路径
            first_page: 起始页码(从1开始)
            last_page: 结束页码(从1开始)
            
        Returns:
            图片字节数据列表
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self.convert_to_bytes,
            pdf_path,
            first_page,
            last_page
        )
    
    async def convert_to_base64_async(
        self,
        pdf_path: str,
        first_page: Optional[int] = None,
        last_page: Optional[int] = None
    ) -> List[str]:
        """
        异步转换PDF文件路径为Base64编码的图片数据
        
        Args:
            pdf_path: PDF文件路径
            first_page: 起始页码(从1开始)
            last_page: 结束页码(从1开始)
            
        Returns:
            Base64编码的图片数据列表
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self.convert_to_base64,
            pdf_path,
            first_page,
            last_page
        )
    
    async def convert_to_bytes_streaming_async(
        self,
        pdf_path: str,
        batch_size: Optional[int] = None,
        first_page: Optional[int] = None,
        last_page: Optional[int] = None
    ) -> Iterator[List[bytes]]:
        """
        异步分批流式转换PDF为图片字节数据
        
        Args:
            pdf_path: PDF文件路径
            batch_size: 每批处理的页数，默认使用配置中的值
            first_page: 起始页码(从1开始)
            last_page: 结束页码(从1开始)
            
        Yields:
            图片字节数据列表的迭代器
        """
        batch_size = batch_size or self.config.batch_size
        
        # 获取总页数
        pdf_info = await self.get_pdf_info_async(pdf_path)
        total_pages = pdf_info["page_count"]
        
        first_page = first_page or 1
        last_page = last_page or total_pages
        
        # 分批处理
        for start in range(first_page, last_page + 1, batch_size):
            end = min(start + batch_size - 1, last_page)
            batch_bytes = await self.convert_to_bytes_async(pdf_path, start, end)
            yield batch_bytes
    
    async def get_pdf_info_async(self, pdf_path: str) -> Dict[str, Any]:
        """
        异步获取PDF文件信息
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            包含PDF信息的字典
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self.get_pdf_info,
            pdf_path
        )
    
    async def get_pdf_page_count_async(self, pdf_path: str) -> int:
        """
        异步获取PDF文件页数的便捷方法
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            PDF文件页数
        """
        info = await self.get_pdf_info_async(pdf_path)
        return info["page_count"]
    
    def close(self):
        """关闭线程池"""
        self.executor.shutdown(wait=True)
    
    async def aclose(self):
        """异步关闭线程池"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.close)


# 创建默认转换器实例
default_converter = PDFToImageConverter()


# 便捷函数
def convert_pdf_to_images(
    pdf_path: str,
    output_folder: Optional[str] = None,
    dpi: int = 200,
    output_format: str = "PNG",
    first_page: Optional[int] = None,
    last_page: Optional[int] = None,
) -> Union[List[str], ImageList]:
    """
    将PDF转换为图片的便捷函数
    
    Args:
        pdf_path: PDF文件路径
        output_folder: 输出文件夹
        dpi: 图片分辨率
        output_format: 输出格式，支持PNG/JPEG
        first_page: 起始页码(从1开始)
        last_page: 结束页码(从1开始)
        
    Returns:
        ImageList对象，支持上下文管理器自动释放资源
    """
    config = PDFConversionConfig(dpi=dpi, output_format=output_format)
    converter = PDFToImageConverter(config)
    
    # 只转换，不保存到磁盘
    return converter.convert_from_path(
        pdf_path=pdf_path,
        first_page=first_page,
        last_page=last_page
    )
        


def convert_pdf_bytes_to_images(
    pdf_bytes: bytes,
    dpi: int = 200,
    output_format: str = "PNG",
    first_page: Optional[int] = None,
    last_page: Optional[int] = None
) -> ImageList:
    """
    将PDF字节数据转换为图片的便捷函数
    
    Args:
        pdf_bytes: PDF文件字节数据
        dpi: 图片分辨率
        output_format: 输出格式，支持PNG/JPEG
        first_page: 起始页码(从1开始)
        last_page: 结束页码(从1开始)
        
    Returns:
        ImageList对象，支持上下文管理器自动释放资源
    """
    config = PDFConversionConfig(dpi=dpi, output_format=output_format)
    converter = PDFToImageConverter(config)
    
    return converter.convert_from_bytes(
        pdf_bytes=pdf_bytes,
        first_page=first_page,
        last_page=last_page
    )


def convert_pdf_to_image_bytes(
    pdf_path: str,
    dpi: int = 200,
    output_format: str = "PNG",
    first_page: Optional[int] = None,
    last_page: Optional[int] = None
) -> List[bytes]:
    """
    将PDF转换为图片字节数据的便捷函数
    
    Args:
        pdf_path: PDF文件路径
        dpi: 图片分辨率
        output_format: 输出格式，支持PNG/JPEG
        first_page: 起始页码(从1开始)
        last_page: 结束页码(从1开始)
        
    Returns:
        图片字节数据列表
    """
    config = PDFConversionConfig(dpi=dpi, output_format=output_format)
    converter = PDFToImageConverter(config)
    
    return converter.convert_to_bytes(
        pdf_path=pdf_path,
        first_page=first_page,
        last_page=last_page
    )


def convert_pdf_to_base64_images(
    pdf_path: str,
    dpi: int = 200,
    output_format: str = "PNG",
    first_page: Optional[int] = None,
    last_page: Optional[int] = None
) -> List[str]:
    """
    将PDF转换为Base64编码图片的便捷函数
    
    Args:
        pdf_path: PDF文件路径
        dpi: 图片分辨率
        output_format: 输出格式，支持PNG/JPEG
        first_page: 起始页码(从1开始)
        last_page: 结束页码(从1开始)
        
    Returns:
        Base64编码的图片数据列表
    """
    config = PDFConversionConfig(dpi=dpi, output_format=output_format)
    converter = PDFToImageConverter(config)
    
    return converter.convert_to_base64(
        pdf_path=pdf_path,
        first_page=first_page,
        last_page=last_page
    )


def get_pdf_page_count(pdf_path: str) -> int:
    """
    获取PDF文件页数的便捷函数
    
    Args:
        pdf_path: PDF文件路径
        
    Returns:
        PDF文件页数
    """
    converter = PDFToImageConverter()
    return converter.get_pdf_page_count(pdf_path)
