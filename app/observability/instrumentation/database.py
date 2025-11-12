"""
数据库操作日志

通过SQLAlchemy Event Listeners自动记录数据库操作
"""
import time
from sqlalchemy import event
from sqlalchemy.engine import Engine
import structlog

logger = structlog.get_logger(__name__)


def setup_database_logging(
    engine: Engine,
    log_queries: bool = True,
    slow_query_threshold_ms: float = 100
) -> None:
    """
    配置数据库日志
    
    Args:
        engine: SQLAlchemy引擎
        log_queries: 是否记录所有查询（False则只记录慢查询）
        slow_query_threshold_ms: 慢查询阈值（毫秒）
    """
    
    @event.listens_for(engine.sync_engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        """查询执行前"""
        context._query_start_time = time.time()
    
    @event.listens_for(engine.sync_engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        """查询执行后"""
        duration = time.time() - context._query_start_time
        duration_ms = duration * 1000
        is_slow = duration_ms > slow_query_threshold_ms
        # 根据配置决定是否记录
        should_log = log_queries or is_slow
        
        if should_log:
            # 截断SQL（避免太长）
            sql = statement
            # 记录查询日志
            log_level = "warning" if is_slow else "info"
            log_func = getattr(logger, log_level)
            log_func(
                "database_query",
                sql=sql,
                duration_ms=round(duration_ms, 2),
                is_slow=is_slow,
                parameters=parameters
            )

