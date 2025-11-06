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
    PORT: int = 8000
    
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
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24
    
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
    
    # RPA配置
    RPA_HEADLESS: bool = True
    RPA_RATE_LIMIT: int = 100
    
    # 多语言配置
    SUPPORTED_LANGUAGES: str = "en,zh,id"
    DEFAULT_LANGUAGE: str = "en"
    
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

