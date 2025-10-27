"""
Logging setup and configuration
"""
import logging
import structlog
from pythonjsonlogger import jsonlogger

from app.core.config import settings


def setup_logging() -> None:
    """配置结构化日志"""
    
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
    
    if settings.LOG_RENDERER == "json":
        # 配置JSON格式的日志
        handler = logging.StreamHandler()
        # 使用python-json-logger进行格式化
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d',
            timestamp=True
        )
        handler.setFormatter(formatter)
        
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.addHandler(handler)
        root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
        
        # structlog与标准logging集成
        processors.append(structlog.stdlib.ProcessorFormatter.wrap_for_formatter)
        
    else:
        # 配置适合开发的控制台日志
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

