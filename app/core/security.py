"""
Security utilities for authentication and authorization
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jose import JWTError, jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHash
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials

from app.core.config import settings


# 使用 Argon2 作为密码哈希算法（现代且安全的选择）
pwd_hasher = PasswordHasher(
    time_cost=2,       # 迭代次数
    memory_cost=65536, # 内存使用量 (64 MB)
    parallelism=2,     # 并行度
    hash_len=32,       # 哈希长度
    salt_len=16        # 盐长度
)


class HTTPBearerAuth(HTTPBearer):
    """自定义HTTPBearer，返回401而不是403"""
    
    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        try:
            return await super().__call__(request)
        except HTTPException as e:
            # 将403转换为401
            if e.status_code == status.HTTP_403_FORBIDDEN:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            raise


# HTTP Bearer认证
security = HTTPBearerAuth()


class SecurityManager:
    """安全管理器"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def create_access_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        生成JWT Token
        
        Args:
            data: Token数据（通常包含user_id, tenant_id等）
            expires_delta: 过期时间增量
        
        Returns:
            JWT Token字符串
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)
        
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        验证Token
        
        Args:
            token: JWT Token字符串
        
        Returns:
            Token载荷数据
        
        Raises:
            HTTPException: Token无效或过期
        """
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            return payload
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            ) from e
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        哈希密码（使用 Argon2）
        
        Args:
            password: 明文密码
        
        Returns:
            哈希后的密码
        """
        return pwd_hasher.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        验证密码（使用 Argon2）
        
        Args:
            plain_password: 明文密码
            hashed_password: 哈希密码
        
        Returns:
            密码是否匹配
        """
        try:
            pwd_hasher.verify(hashed_password, plain_password)
            return True
        except (VerifyMismatchError, InvalidHash):
            return False


# 全局安全管理器实例
security_manager = SecurityManager(
    secret_key=settings.SECRET_KEY,
    algorithm=settings.ALGORITHM
)

