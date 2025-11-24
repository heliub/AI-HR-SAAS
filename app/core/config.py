"""
Application Configuration
"""
from typing import List, Optional, Dict
from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    """应用配置"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )
    
    # 基础配置
    APP_NAME: str = "HR SAAS"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # 服务配置
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    
    # 数据库配置
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    
    # Redis配置
    REDIS_URL: str
    REDIS_MAX_CONNECTIONS: int = 50
    
    # Celery配置
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    
    # MinIO配置
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str = "hr-saas-files"
    MINIO_SECURE: bool = False
    
    # JWT配置
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24 * 30
    
    # AI配置
    AI_PROVIDERS: List[Dict] = [
        {
            "provider": "volcengine",
            "base_url": "https://ark.cn-beijing.volces.com/api/v3"
        },
        {
            "provider": "openai"        
        }
    ]
    EMBEDDING_PROVIDERS: List[Dict] = [
        {
            "provider": "volcengine",
            "base_url": "https://ark.cn-beijing.volces.com/api/v3"
        }
    ]
    
    # Jaeger配置
    JAEGER_HOST: str = "localhost"
    JAEGER_PORT: int = 6831
    JAEGER_ENABLED: bool = False
    JAEGER_OTLP_ENDPOINT_HTTP: str = "http://localhost:4318/v1/traces"
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_RENDERER: str = "json"  # console or json
    LOG_TO_FILE: bool = True  # 是否写入文件
    LOG_FILE_PATH: str = "logs/app.log"  # 日志文件路径
    LOG_FILE_MAX_BYTES: int = 100 * 1024 * 1024  # 单个日志文件最大大小（100MB）
    LOG_FILE_BACKUP_COUNT: int = 10  # 保留的备份文件数量
    LOG_MAX_BODY_SIZE: int = 10000  # 最大body记录大小（字节）
    LOG_MAX_STRING_LENGTH: int = 1000  # 最大字符串长度
    
    # 数据库日志配置
    LOG_DATABASE_QUERIES: bool = True  # 是否记录所有SQL查询
    SLOW_QUERY_THRESHOLD_MS: float = 100  # 慢查询阈值（毫秒）
    
    # RPA配置
    RPA_HEADLESS: bool = True
    RPA_RATE_LIMIT: int = 100
    
    # 多语言配置
    SUPPORTED_LANGUAGES: str = "en,zh,id"
    DEFAULT_LANGUAGE: str = "en"

    VOLCENGINE_API_KEY: str
    OPENAI_API_KEY: str
    
    @validator("SUPPORTED_LANGUAGES")
    def parse_languages(cls, v):
        """解析支持的语言列表"""
        if isinstance(v, str):
            return [lang.strip() for lang in v.split(",")]
        return v
    
    @property
    def supported_languages_list(self) -> List[str]:
        """获取支持的语言列表"""
        if isinstance(self.SUPPORTED_LANGUAGES, str):
            return [lang.strip() for lang in self.SUPPORTED_LANGUAGES.split(",")]
        return self.SUPPORTED_LANGUAGES
    
settings = Settings()

