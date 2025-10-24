"""
Encryption utilities for sensitive data
"""
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2

from app.core.config import settings


class EncryptionManager:
    """加密管理器"""
    
    def __init__(self, secret_key: str):
        # 使用PBKDF2从secret_key派生加密密钥
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'hr_saas_salt',  # 在生产环境应该使用独立的salt
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
        self.cipher = Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """
        加密字符串
        
        Args:
            data: 明文字符串
        
        Returns:
            加密后的字符串（Base64编码）
        """
        encrypted = self.cipher.encrypt(data.encode())
        return encrypted.decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        解密字符串
        
        Args:
            encrypted_data: 加密的字符串（Base64编码）
        
        Returns:
            解密后的明文字符串
        """
        decrypted = self.cipher.decrypt(encrypted_data.encode())
        return decrypted.decode()


# 全局加密管理器实例
_encryption_manager: EncryptionManager = None


def get_encryption_manager() -> EncryptionManager:
    """获取加密管理器实例"""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager(settings.SECRET_KEY)
    return _encryption_manager

