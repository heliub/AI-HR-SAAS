"""
Storage base interface
"""
from abc import ABC, abstractmethod
from typing import BinaryIO, Optional


class BaseStorageClient(ABC):
    """存储客户端抽象基类"""
    
    @abstractmethod
    async def upload(
        self, 
        file: BinaryIO, 
        object_name: str,
        content_type: Optional[str] = None
    ) -> str:
        """
        上传文件
        
        Args:
            file: 文件对象
            object_name: 对象名称/路径
            content_type: 内容类型
        
        Returns:
            文件访问URL或Key
        """
        pass
    
    @abstractmethod
    async def download(self, object_name: str) -> bytes:
        """
        下载文件
        
        Args:
            object_name: 对象名称/路径
        
        Returns:
            文件内容（字节）
        """
        pass
    
    @abstractmethod
    async def delete(self, object_name: str) -> bool:
        """
        删除文件
        
        Args:
            object_name: 对象名称/路径
        
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def exists(self, object_name: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            object_name: 对象名称/路径
        
        Returns:
            文件是否存在
        """
        pass
    
    @abstractmethod
    async def get_url(self, object_name: str, expires: int = 3600) -> str:
        """
        获取文件预签名URL
        
        Args:
            object_name: 对象名称/路径
            expires: 过期时间（秒）
        
        Returns:
            预签名URL
        """
        pass

