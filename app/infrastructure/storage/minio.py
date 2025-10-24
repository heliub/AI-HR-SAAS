"""
MinIO storage client implementation
"""
from typing import BinaryIO, Optional
from datetime import timedelta
import io

from minio import Minio
from minio.error import S3Error

from app.core.config import settings
from app.infrastructure.storage.base import BaseStorageClient


class MinIOClient(BaseStorageClient):
    """MinIO存储客户端"""
    
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        self.bucket = settings.MINIO_BUCKET
        self._ensure_bucket()
    
    def _ensure_bucket(self) -> None:
        """确保bucket存在"""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except S3Error as e:
            raise RuntimeError(f"Failed to ensure bucket: {e}")
    
    async def upload(
        self, 
        file: BinaryIO, 
        object_name: str,
        content_type: Optional[str] = None
    ) -> str:
        """上传文件"""
        try:
            # 获取文件大小
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(0)
            
            # 上传文件
            self.client.put_object(
                self.bucket,
                object_name,
                file,
                file_size,
                content_type=content_type,
            )
            
            return object_name
        except S3Error as e:
            raise RuntimeError(f"Failed to upload file: {e}")
    
    async def download(self, object_name: str) -> bytes:
        """下载文件"""
        try:
            response = self.client.get_object(self.bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            raise RuntimeError(f"Failed to download file: {e}")
    
    async def delete(self, object_name: str) -> bool:
        """删除文件"""
        try:
            self.client.remove_object(self.bucket, object_name)
            return True
        except S3Error as e:
            if e.code == "NoSuchKey":
                return False
            raise RuntimeError(f"Failed to delete file: {e}")
    
    async def exists(self, object_name: str) -> bool:
        """检查文件是否存在"""
        try:
            self.client.stat_object(self.bucket, object_name)
            return True
        except S3Error as e:
            if e.code == "NoSuchKey":
                return False
            raise RuntimeError(f"Failed to check file existence: {e}")
    
    async def get_url(self, object_name: str, expires: int = 3600) -> str:
        """获取预签名URL"""
        try:
            url = self.client.presigned_get_object(
                self.bucket,
                object_name,
                expires=timedelta(seconds=expires),
            )
            return url
        except S3Error as e:
            raise RuntimeError(f"Failed to generate presigned URL: {e}")


# 全局存储客户端实例
_storage_client: Optional[MinIOClient] = None


def get_storage_client() -> MinIOClient:
    """获取存储客户端实例"""
    global _storage_client
    if _storage_client is None:
        _storage_client = MinIOClient()
    return _storage_client

