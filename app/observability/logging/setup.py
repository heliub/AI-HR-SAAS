"""
Logging setup and configuration
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional
import structlog
from pythonjsonlogger import jsonlogger

from app.core.config import settings


def _create_json_formatter(include_pathname: bool = True) -> jsonlogger.JsonFormatter:
    """创建JSON formatter"""
    fmt = '%(asctime)s %(name)s %(levelname)s %(message)s'
    if include_pathname:
        fmt += ' %(pathname)s %(lineno)d'
    # 添加ensure_ascii=False参数，确保中文字符不被转义
    return jsonlogger.JsonFormatter(fmt, timestamp=True, ensure_ascii=False)


def _create_file_handler(formatter: Optional[logging.Formatter] = None) -> RotatingFileHandler:
    """创建文件handler（自动创建目录）"""
    log_dir = os.path.dirname(settings.LOG_FILE_PATH)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    handler = RotatingFileHandler(
        settings.LOG_FILE_PATH,
        maxBytes=settings.LOG_FILE_MAX_BYTES,
        backupCount=settings.LOG_FILE_BACKUP_COUNT,
        encoding='utf-8'
    )
    if formatter:
        handler.setFormatter(formatter)
    return handler


def setup_logging() -> None:
    """配置结构化日志"""
    # 基础processors
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    # 配置根logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # 根据渲染模式配置handlers
    is_json = settings.LOG_RENDERER == "json"
    
    # 控制台handler
    console_handler = logging.StreamHandler()
    if is_json:
        console_handler.setFormatter(_create_json_formatter())
    root_logger.addHandler(console_handler)
    
    # 文件handler（始终使用JSON格式）
    if settings.LOG_TO_FILE:
        file_handler = _create_file_handler(_create_json_formatter(include_pathname=False))
        root_logger.addHandler(file_handler)
    
    # 配置structlog
    if is_json:
        processors.append(structlog.stdlib.ProcessorFormatter.wrap_for_formatter)
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = None):
    """获取logger实例"""
    return structlog.get_logger(name)

