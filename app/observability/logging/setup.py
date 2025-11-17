"""
Logging setup and configuration

使用 structlog 实现结构化日志，支持：
- 控制台：开发模式彩色输出 / 生产模式JSON输出
- 文件：始终JSON格式输出
- 完整的context绑定和异常追踪
"""
import logging
import os
from logging.handlers import RotatingFileHandler
import structlog

from app.core.config import settings


def _create_file_handler() -> RotatingFileHandler:
    """创建文件handler（自动创建目录）"""
    log_dir = os.path.dirname(settings.LOG_FILE_PATH)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    return RotatingFileHandler(
        settings.LOG_FILE_PATH,
        maxBytes=settings.LOG_FILE_MAX_BYTES,
        backupCount=settings.LOG_FILE_BACKUP_COUNT,
        encoding='utf-8'
    )


def setup_logging() -> None:
    """配置结构化日志
    
    架构说明：
    1. structlog 负责结构化数据处理和渲染
    2. ProcessorFormatter 将 structlog 的 processors 桥接到标准库 logging
    3. 控制台和文件都使用 structlog 的渲染器（JSONRenderer/ConsoleRenderer）
    
    这是 structlog 官方推荐的标准集成方式，简洁且功能完整。
    """
    # 配置根logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # 共享的 processors - 用于数据处理（不包含渲染）
    # 这些会被 ProcessorFormatter 的 foreign_pre_chain 使用，处理非 structlog 的日志
    shared_processors = [
        structlog.contextvars.merge_contextvars,  # 合并 context variables
        structlog.stdlib.add_logger_name,  # 添加 logger 名称
        structlog.stdlib.add_log_level,  # 添加日志级别
        structlog.stdlib.ExtraAdder(),  # 将 extra 参数添加到事件字典
        structlog.processors.TimeStamper(fmt="iso"),  # ISO 格式时间戳
        structlog.processors.StackInfoRenderer(),  # 渲染堆栈信息
        structlog.processors.format_exc_info,  # 格式化异常信息
        structlog.processors.UnicodeDecoder(),  # 解码 Unicode
    ]
    
    # 根据配置决定渲染模式
    is_json = settings.LOG_RENDERER == "json"
    
    # 控制台 handler
    console_handler = logging.StreamHandler()
    if is_json:
        # 生产模式：JSON 输出
        console_handler.setFormatter(
            structlog.stdlib.ProcessorFormatter(
                foreign_pre_chain=shared_processors,
                processors=[
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.processors.JSONRenderer(ensure_ascii=False),  # 支持中文
                ],
            )
        )
    else:
        # 开发模式：彩色控制台输出
        console_handler.setFormatter(
            structlog.stdlib.ProcessorFormatter(
                foreign_pre_chain=shared_processors,
                processors=[
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.dev.ConsoleRenderer(colors=True),
                ],
            )
        )
    root_logger.addHandler(console_handler)
    
    # 文件 handler（始终使用 JSON 格式）
    if settings.LOG_TO_FILE:
        file_handler = _create_file_handler()
        file_handler.setFormatter(
            structlog.stdlib.ProcessorFormatter(
                foreign_pre_chain=shared_processors,
                processors=[
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.processors.JSONRenderer(ensure_ascii=False),  # 支持中文
                ],
            )
        )
        root_logger.addHandler(file_handler)
    
    # 配置 structlog（用于 structlog.get_logger() 创建的 logger）
    structlog.configure(
        processors=shared_processors + [
            # 这个 processor 将事件字典包装成适合 ProcessorFormatter 的格式
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = None):
    """获取logger实例"""
    return structlog.get_logger(name)

