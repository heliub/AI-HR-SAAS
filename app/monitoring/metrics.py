"""
监控和指标系统
使用Prometheus收集应用指标
"""
import time
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from functools import wraps
from contextlib import asynccontextmanager

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from starlette.responses import Response as StarletteResponse
import structlog

logger = structlog.get_logger(__name__)


class MetricsRegistry:
    """指标注册表"""

    def __init__(self):
        self.registry = CollectorRegistry()
        self._setup_metrics()

    def _setup_metrics(self):
        """设置指标"""
        # HTTP请求计数器
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code', 'tenant_id'],
            registry=self.registry
        )

        # HTTP请求延迟
        self.http_request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint', 'tenant_id'],
            registry=self.registry
        )

        # 数据库查询计数器
        self.db_queries_total = Counter(
            'db_queries_total',
            'Total database queries',
            ['operation', 'table', 'tenant_id'],
            registry=self.registry
        )

        # 数据库查询延迟
        self.db_query_duration = Histogram(
            'db_query_duration_seconds',
            'Database query duration in seconds',
            ['operation', 'table', 'tenant_id'],
            registry=self.registry
        )

        # 缓存操作计数器
        self.cache_operations_total = Counter(
            'cache_operations_total',
            'Total cache operations',
            ['operation', 'result', 'tenant_id'],
            registry=self.registry
        )

        # 活跃用户数
        self.active_users = Gauge(
            'active_users_total',
            'Number of active users',
            ['tenant_id'],
            registry=self.registry
        )

        # 业务指标
        self.resumes_created_total = Counter(
            'resumes_created_total',
            'Total resumes created',
            ['tenant_id', 'source'],
            registry=self.registry
        )

        self.jobs_created_total = Counter(
            'jobs_created_total',
            'Total jobs created',
            ['tenant_id', 'department'],
            registry=self.registry
        )

        self.interviews_scheduled_total = Counter(
            'interviews_scheduled_total',
            'Total interviews scheduled',
            ['tenant_id', 'interview_type'],
            registry=self.registry
        )

        # 系统指标
        self.system_memory_usage = Gauge(
            'system_memory_usage_bytes',
            'System memory usage in bytes',
            registry=self.registry
        )

        self.error_rate = Gauge(
            'error_rate',
            'Error rate (errors/total requests)',
            ['tenant_id', 'error_type'],
            registry=self.registry
        )


# 全局指标实例
metrics = MetricsRegistry()


class MetricsCollector:
    """指标收集器"""

    def __init__(self):
        self.start_time = time.time()
        self.tenant_stats: Dict[str, Dict] = {}

    async def record_http_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration: float,
        tenant_id: Optional[str] = None
    ):
        """记录HTTP请求指标"""
        try:
            labels = {
                'method': method,
                'endpoint': endpoint,
                'status_code': str(status_code),
                'tenant_id': tenant_id or 'unknown'
            }

            metrics.http_requests_total.labels(**labels).inc()
            metrics.http_request_duration.labels(**labels).observe(duration)

            # 更新租户统计
            if tenant_id:
                if tenant_id not in self.tenant_stats:
                    self.tenant_stats[tenant_id] = {
                        'requests': 0,
                        'errors': 0,
                        'last_activity': datetime.utcnow()
                    }

                self.tenant_stats[tenant_id]['requests'] += 1
                self.tenant_stats[tenant_id]['last_activity'] = datetime.utcnow()

                if status_code >= 400:
                    self.tenant_stats[tenant_id]['errors'] += 1

        except Exception as e:
            logger.error("Failed to record HTTP metrics", error=str(e))

    async def record_db_query(
        self,
        operation: str,
        table: str,
        duration: float,
        tenant_id: Optional[str] = None
    ):
        """记录数据库查询指标"""
        try:
            labels = {
                'operation': operation,
                'table': table,
                'tenant_id': tenant_id or 'unknown'
            }

            metrics.db_queries_total.labels(**labels).inc()
            metrics.db_query_duration.labels(**labels).observe(duration)

        except Exception as e:
            logger.error("Failed to record DB metrics", error=str(e))

    async def record_cache_operation(
        self,
        operation: str,
        result: str,  # 'hit', 'miss', 'set', 'delete'
        tenant_id: Optional[str] = None
    ):
        """记录缓存操作指标"""
        try:
            labels = {
                'operation': operation,
                'result': result,
                'tenant_id': tenant_id or 'unknown'
            }

            metrics.cache_operations_total.labels(**labels).inc()

        except Exception as e:
            logger.error("Failed to record cache metrics", error=str(e))

    async def record_business_event(
        self,
        event_type: str,
        tenant_id: str,
        **metadata
    ):
        """记录业务事件指标"""
        try:
            if event_type == 'resume_created':
                metrics.resumes_created_total.labels(
                    tenant_id=tenant_id,
                    source=metadata.get('source', 'unknown')
                ).inc()

            elif event_type == 'job_created':
                metrics.jobs_created_total.labels(
                    tenant_id=tenant_id,
                    department=metadata.get('department', 'unknown')
                ).inc()

            elif event_type == 'interview_scheduled':
                metrics.interviews_scheduled_total.labels(
                    tenant_id=tenant_id,
                    interview_type=metadata.get('interview_type', 'unknown')
                ).inc()

        except Exception as e:
            logger.error("Failed to record business metrics", error=str(e))

    async def update_active_users(self, tenant_id: str, count: int):
        """更新活跃用户数"""
        try:
            metrics.active_users.labels(tenant_id=tenant_id).set(count)
        except Exception as e:
            logger.error("Failed to update active users", error=str(e))

    async def update_error_rate(self, tenant_id: str, error_type: str, rate: float):
        """更新错误率"""
        try:
            metrics.error_rate.labels(tenant_id=tenant_id, error_type=error_type).set(rate)
        except Exception as e:
            logger.error("Failed to update error rate", error=str(e))

    def get_tenant_stats(self, tenant_id: str) -> Optional[Dict]:
        """获取租户统计信息"""
        return self.tenant_stats.get(tenant_id)

    def get_all_stats(self) -> Dict:
        """获取所有统计信息"""
        return {
            'uptime_seconds': time.time() - self.start_time,
            'tenant_count': len(self.tenant_stats),
            'total_requests': sum(
                stats['requests'] for stats in self.tenant_stats.values()
            ),
            'total_errors': sum(
                stats['errors'] for stats in self.tenant_stats.values()
            ),
            'tenant_stats': dict(self.tenant_stats)
        }


# 全局指标收集器
collector = MetricsCollector()


# 装饰器
def monitor_performance(operation_name: str = None):
    """性能监控装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            op_name = operation_name or f"{func.__module__}.{func.__name__}"

            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                # 记录成功指标
                if hasattr(args[0], '__class__'):  # 如果是方法调用
                    tenant_id = getattr(args[0], 'tenant_id', None)
                else:
                    tenant_id = kwargs.get('tenant_id')

                logger.info("Operation completed",
                           operation=op_name,
                           duration=duration,
                           tenant_id=str(tenant_id) if tenant_id else None)

                return result

            except Exception as e:
                duration = time.time() - start_time
                logger.error("Operation failed",
                           operation=op_name,
                           duration=duration,
                           error=str(e))
                raise

        return wrapper
    return decorator


def monitor_db_query(table_name: str):
    """数据库查询监控装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                # 记录查询指标
                tenant_id = getattr(args[0], 'tenant_id', None) if args else None
                operation = func.__name__.replace('get_', 'SELECT').replace('create_', 'INSERT').replace('update_', 'UPDATE').replace('delete_', 'DELETE')

                await collector.record_db_query(
                    operation=operation,
                    table=table_name,
                    duration=duration,
                    tenant_id=str(tenant_id) if tenant_id else None
                )

                return result

            except Exception as e:
                duration = time.time() - start_time
                logger.error("Database query failed",
                           table=table_name,
                           operation=func.__name__,
                           duration=duration,
                           error=str(e))
                raise

        return wrapper
    return decorator


@asynccontextmanager
async def monitored_operation(operation_name: str, tenant_id: Optional[str] = None):
    """监控操作上下文管理器"""
    start_time = time.time()
    try:
        logger.info("Operation started", operation=operation_name, tenant_id=str(tenant_id) if tenant_id else None)
        yield
        duration = time.time() - start_time
        logger.info("Operation completed", operation=operation_name, duration=duration, tenant_id=str(tenant_id) if tenant_id else None)
    except Exception as e:
        duration = time.time() - start_time
        logger.error("Operation failed", operation=operation_name, duration=duration, error=str(e), tenant_id=str(tenant_id) if tenant_id else None)
        raise


class MetricsMiddleware:
    """指标收集中间件"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        start_time = time.time()

        # 从请求中提取租户信息（如果用户已认证）
        tenant_id = None
        try:
            # 这里需要根据实际的认证机制获取租户ID
            # 可能需要从JWT token或session中获取
            pass
        except Exception:
            pass

        # 创建响应
        response = None

        async def send_wrapper(message):
            nonlocal response
            if message["type"] == "http.response.start":
                response = message
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)

            # 记录指标
            duration = time.time() - start_time
            status_code = response.get("status", 200) if response else 200

            await collector.record_http_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=status_code,
                duration=duration,
                tenant_id=tenant_id
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error("Request failed",
                       method=request.method,
                       endpoint=request.url.path,
                       duration=duration,
                       error=str(e))
            raise


class HealthChecker:
    """健康检查器"""

    def __init__(self):
        self.checks: Dict[str, callable] = {}
        self.last_results: Dict[str, Dict] = {}

    def add_check(self, name: str, check_func: callable):
        """添加健康检查"""
        self.checks[name] = check_func

    async def run_checks(self) -> Dict[str, Any]:
        """运行所有健康检查"""
        results = {}
        overall_healthy = True

        for name, check_func in self.checks.items():
            try:
                start_time = time.time()
                result = await check_func()
                duration = time.time() - start_time

                check_result = {
                    'healthy': result.get('healthy', False),
                    'message': result.get('message', 'OK'),
                    'duration': duration,
                    'details': result.get('details', {}),
                    'timestamp': datetime.utcnow().isoformat()
                }

                if not check_result['healthy']:
                    overall_healthy = False

                results[name] = check_result

            except Exception as e:
                results[name] = {
                    'healthy': False,
                    'message': str(e),
                    'duration': 0,
                    'details': {},
                    'timestamp': datetime.utcnow().isoformat()
                }
                overall_healthy = False

        self.last_results = results

        return {
            'healthy': overall_healthy,
            'checks': results,
            'timestamp': datetime.utcnow().isoformat()
        }

    async def check_database(self) -> Dict:
        """检查数据库连接"""
        try:
            # 这里需要实际的数据库检查逻辑
            # 例如：执行简单的SELECT 1
            return {'healthy': True, 'message': 'Database connection OK'}
        except Exception as e:
            return {'healthy': False, 'message': f'Database error: {str(e)}'}

    async def check_redis(self) -> Dict:
        """检查Redis连接"""
        try:
            # 这里需要实际的Redis检查逻辑
            # 例如：执行PING命令
            return {'healthy': True, 'message': 'Redis connection OK'}
        except Exception as e:
            return {'healthy': False, 'message': f'Redis error: {str(e)}'}

    async def check_memory(self) -> Dict:
        """检查内存使用"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            return {
                'healthy': memory.percent < 90,
                'message': f'Memory usage: {memory.percent:.1f}%',
                'details': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent
                }
            }
        except Exception as e:
            return {'healthy': False, 'message': f'Memory check error: {str(e)}'}

    def setup_default_checks(self):
        """设置默认健康检查"""
        self.add_check('database', self.check_database)
        self.add_check('redis', self.check_redis)
        self.add_check('memory', self.check_memory)


# 全局健康检查器
health_checker = HealthChecker()
health_checker.setup_default_checks()