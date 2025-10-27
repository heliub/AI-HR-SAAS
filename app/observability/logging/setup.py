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

    # 添加OpenTelemetry trace上下文处理器（如果启用tracing）
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import _Span
        from structlog.processors import add_log_level

        def add_trace_context(logger, method_name: str, event_dict: dict) -> dict:
            """添加trace上下文到日志中"""
            current_span = trace.get_current_span()
            if current_span is not None:
                span_context = current_span.get_span_context()
                # 检查trace_id不为0（有效的span）
                if span_context and hasattr(span_context, 'trace_id') and span_context.trace_id != 0:
                    event_dict["trace_id"] = format(span_context.trace_id, "032x")
                    event_dict["span_id"] = format(span_context.span_id, "016x")
                    event_dict["trace_flags"] = span_context.trace_flags
            return event_dict

        processors.append(add_trace_context)
    except ImportError:
        # 如果OpenTelemetry不可用，跳过trace上下文
        pass
    
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

