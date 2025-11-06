"""
图片保存工具类
支持批量、单个图片保存，支持Image、字节码、base64多种格式，预留云端保存能力
"""

import os
import base64
import tempfile
import uuid
from io import BytesIO
from typing import List, Optional, Union, Dict, Any
from abc import ABC, abstractmethod
import time
from PIL import Image
import structlog


logger = structlog.get_logger(__name__)


class StorageBackend(ABC):
    """存储后端抽象基类，用于扩展不同的存储方式"""
    
    @abstractmethod
    def save(self, data: bytes, path: str) -> str:
        """
        保存数据到指定路径
        
        Args:
            data: 要保存的字节数据
            path: 保存路径
            
        Returns:
            实际保存的路径或URL
        """
        pass


class LocalStorageBackend(StorageBackend):
    """本地存储后端实现"""
    
    def save(self, data: bytes, path: str) -> str:
        """
        保存数据到本地文件系统
        
        Args:
            data: 要保存的字节数据
            path: 保存路径
            
        Returns:
            实际保存的路径
        """
        if not data:
            raise ValueError("要保存的数据不能为空")
        
        if not path:
            raise ValueError("保存路径不能为空")
        
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            with open(path, 'wb') as f:
                f.write(data)
            
            return path
        except Exception as e:
            logger.error("本地文件保存失败", path=path, error=str(e))
            raise RuntimeError(f"本地文件保存失败: {str(e)}")


class CloudStorageBackend(StorageBackend):
    """云端存储后端实现（示例）"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化云端存储后端
        
        Args:
            config: 云端存储配置，如API密钥、桶名等
        """
        self.config = config or {}
        # 这里可以初始化具体的云存储客户端，如AWS S3、阿里云OSS等
        # 示例：self.client = boto3.client('s3', **self.config)
    
    def save(self, data: bytes, path: str) -> str:
        """
        保存数据到云端存储
        
        Args:
            data: 要保存的字节数据
            path: 保存路径
            
        Returns:
            云端资源的URL
        """
        if not data:
            raise ValueError("要保存的数据不能为空")
        
        if not path:
            raise ValueError("保存路径不能为空")
        
        try:
            # 这里实现具体的云端存储逻辑
            # 示例：
            # bucket = self.config.get('bucket')
            # self.client.put_object(Bucket=bucket, Key=path, Body=data)
            # return f"https://{bucket}.s3.amazonaws.com/{path}"
            
            # 暂时返回模拟URL
            logger.info("云端保存（模拟）", path=path, size=len(data))
            return f"https://cloud-storage.example.com/{path}"
        except Exception as e:
            logger.error("云端保存失败", path=path, error=str(e))
            raise RuntimeError(f"云端保存失败: {str(e)}")


class ImageSaver:
    """图片保存工具类"""
    
    # 支持的图片格式
    SUPPORTED_FORMATS = ["PNG", "JPEG", "JPG", "BMP", "TIFF", "GIF", "WEBP"]
    
    def __init__(
        self,
        output_format: str = "PNG",
        quality: int = 85,
        storage_backend: Optional[StorageBackend] = None,
        default_filename_prefix: str = "image"
    ):
        """
        初始化图片保存器
        
        Args:
            output_format: 输出格式，支持PNG/JPEG等，默认PNG
            quality: 图片质量(1-100)，仅对JPEG有效，默认85
            storage_backend: 存储后端，默认使用本地存储
            default_filename_prefix: 默认文件名前缀
        """
        # 验证输出格式
        output_format = output_format.upper()
        if output_format not in self.SUPPORTED_FORMATS:
            raise ValueError(f"不支持的输出格式: {output_format}，支持的格式: {', '.join(self.SUPPORTED_FORMATS)}")
        
        # 验证质量参数
        if not 1 <= quality <= 100:
            raise ValueError(f"图片质量必须在1-100之间，当前值: {quality}")
        
        
        self.output_format = output_format
        self.quality = quality
        self.storage_backend = storage_backend or LocalStorageBackend()
        self.default_filename_prefix = default_filename_prefix
        
    
    def _validate_image(self, image: Union[Image.Image, bytes, str]) -> None:
        """
        验证图片数据
        
        Args:
            image: 图片数据
        """
        if image is None:
            raise ValueError("图片数据不能为None")
        
        if isinstance(image, bytes) and len(image) == 0:
            raise ValueError("图片字节数据不能为空")
        
        if isinstance(image, str) and not image.strip():
            raise ValueError("图片字符串不能为空")
    
    def _convert_to_bytes(self, image: Union[Image.Image, bytes, str]) -> bytes:
        """
        将不同格式的图片转换为字节数据
        
        Args:
            image: PIL Image对象、字节数据或Base64字符串
            
        Returns:
            图片字节数据
        """
        # 验证输入
        self._validate_image(image)
        
        if isinstance(image, bytes):
            return image
        
        if isinstance(image, str):
            # 假设是Base64字符串
            try:
                # 处理带data URL前缀的Base64
                if image.startswith('data:image'):
                    # 分割并获取Base64部分
                    parts = image.split(',')
                    if len(parts) < 2:
                        raise ValueError("无效的data URL格式")
                    image = parts[1]
                
                # 解码Base64
                decoded_data = base64.b64decode(image)
                if not decoded_data:
                    raise ValueError("Base64解码结果为空")
                
                return decoded_data
            except (base64.binascii.Error, ValueError) as e:
                logger.error("Base64解码失败", error=str(e))
                raise ValueError(f"无效的Base64图片数据: {str(e)}")
        
        if isinstance(image, Image.Image):
            buffer = BytesIO()
            try:
                # 根据输出格式设置保存参数
                save_kwargs = {"format": self.output_format}
                if self.output_format in ["JPEG", "JPG"]:
                    save_kwargs["quality"] = self.quality
                    # JPEG不支持透明度，需要转换为RGB
                    if image.mode in ("RGBA", "LA", "P"):
                        image = image.convert("RGB")
                
                # 保存图片到缓冲区
                image.save(buffer, **save_kwargs)
                return buffer.getvalue()
            finally:
                # 确保缓冲区被关闭
                buffer.close()
        
        raise ValueError(f"不支持的图片类型: {type(image)}")
    
    def _generate_filename(self, filename_prefix: Optional[str] = None, extension: Optional[str] = None) -> str:
        """
        生成文件名
        
        Args:
            filename_prefix: 文件名前缀
            extension: 文件扩展名
            
        Returns:
            生成的文件名
        """
        filename_prefix = filename_prefix or self.default_filename_prefix
        extension = extension or self.output_format.lower()
        
        # 使用UUID确保唯一性
        unique_id = str(uuid.uuid4())[:8]
        return f"{filename_prefix}_{unique_id}.{extension}"
    
    def _is_directory_path(self, path: str) -> bool:
        """
        判断路径是否为目录
        
        Args:
            path: 路径
            
        Returns:
            是否为目录
        """
        # 如果路径以目录分隔符结尾，认为是目录
        if path.endswith('/') or path.endswith('\\'):
            return True
        
        # 如果路径已存在且是目录，返回True
        if os.path.exists(path) and os.path.isdir(path):
            return True
        
        # 如果路径不包含扩展名，可能是目录
        if not os.path.splitext(path)[1]:
            return True
            
        return False
    
    def save_single(
        self,
        image: Union[Image.Image, bytes, str],
        path: str,
        filename: Optional[str] = None
    ) -> str:
        """
        保存单个图片
        
        Args:
            image: PIL Image对象、字节数据或Base64字符串
            path: 保存路径（可以是目录或完整文件路径）
            filename: 文件名（如果path是目录）
            
        Returns:
            实际保存的路径或URL
        """
        # 验证路径
        if not path:
            raise ValueError("保存路径不能为空")
        
        # 转换为字节数据
        image_bytes = self._convert_to_bytes(image)
        
        # 如果path是目录，生成完整文件路径
        if self._is_directory_path(path):
            filename = filename or self._generate_filename()
            full_path = os.path.join(path, filename)
        else:
            full_path = path
        
        # 使用存储后端保存
        return self.storage_backend.save(image_bytes, full_path)
    
    def save_batch(
        self,
        images: List[Union[Image.Image, bytes, str]],
        path: str,
        filename_prefix: Optional[str] = None
    ) -> List[str]:
        """
        批量保存图片
        
        Args:
            images: PIL Image对象列表、字节数据列表或Base64字符串列表
            path: 保存目录
            filename_prefix: 文件名前缀
            
        Returns:
            保存的路径或URL列表
        """
        saved_paths = []
        
        for i, image in enumerate(images):
            filename = self._generate_filename(filename_prefix=f"{filename_prefix}_{i+1}")
            saved_path = self.save_single(image, path, filename)
            saved_paths.append(saved_path)
        
        return saved_paths
    
    def save_to_temp(
        self,
        image: Union[Image.Image, bytes, str],
        filename_prefix: Optional[str] = None
    ) -> str:
        """
        保存单个图片到临时目录
        
        Args:
            image: PIL Image对象、字节数据或Base64字符串
            filename_prefix: 文件名前缀
            
        Returns:
            临时文件路径
        """
        filename = self._generate_filename(filename_prefix=filename_prefix)
        temp_dir = tempfile.gettempdir()
        return self.save_single(image, temp_dir, filename)
    
    def save_batch_to_temp(
        self,
        images: List[Union[Image.Image, bytes, str]],
        filename_prefix: Optional[str] = None
    ) -> List[str]:
        """
        批量保存图片到临时目录
        
        Args:
            images: PIL Image对象列表、字节数据列表或Base64字符串列表
            filename_prefix: 文件名前缀
            
        Returns:
            临时文件路径列表
        """
        temp_dir = tempfile.mkdtemp()
        return self.save_batch(images, temp_dir, filename_prefix)


# 创建默认实例
default_saver = ImageSaver()


# 便捷函数
def save_image(
    image: Union[Image.Image, bytes, str],
    path: str,
    filename: Optional[str] = None,
    output_format: str = "PNG",
    quality: int = 85
) -> str:
    """
    保存单个图片的便捷函数
    
    Args:
        image: PIL Image对象、字节数据或Base64字符串
        path: 保存路径
        filename: 文件名
        output_format: 输出格式
        quality: 图片质量
        
    Returns:
        保存的路径
    """
    saver = ImageSaver(output_format=output_format, quality=quality)
    return saver.save_single(image, path, filename)


def save_images(
    images: List[Union[Image.Image, bytes, str]],
    path: str,
    filename_prefix: str = "image",
    output_format: str = "PNG",
    quality: int = 85
) -> List[str]:
    """
    批量保存图片的便捷函数
    
    Args:
        images: PIL Image对象列表、字节数据列表或Base64字符串列表
        path: 保存目录
        filename_prefix: 文件名前缀
        output_format: 输出格式
        quality: 图片质量
        
    Returns:
        保存的路径列表
    """
    saver = ImageSaver(output_format=output_format, quality=quality)
    return saver.save_batch(images, path, filename_prefix)
