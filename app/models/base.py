"""
Base model with common fields
"""
from datetime import datetime
from typing import Any

from sqlalchemy import Column, BigInteger, DateTime, func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """基础模型类"""
    
    @declared_attr
    def __tablename__(cls) -> str:
        """自动生成表名"""
        return cls.__name__.lower() + 's'
    
    # 通用字段
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(
        DateTime, 
        nullable=False, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow,
        server_default=func.now(),
        server_onupdate=func.now()
    )
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

