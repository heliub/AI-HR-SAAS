"""
Prometheus metrics setup
"""
from prometheus_client import Counter, Histogram, Gauge
from prometheus_client import make_asgi_app
from fastapi import FastAPI

# 定义指标
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
)

active_requests = Gauge(
    'http_active_requests',
    'Number of active HTTP requests',
    ['method', 'endpoint']
)

ai_api_calls_total = Counter(
    'ai_api_calls_total',
    'Total AI API calls',
    ['provider', 'model', 'status']
)

ai_api_duration_seconds = Histogram(
    'ai_api_duration_seconds',
    'AI API call duration in seconds',
    ['provider', 'model']
)

celery_tasks_total = Counter(
    'celery_tasks_total',
    'Total Celery tasks',
    ['task_type', 'status']
)

database_connections = Gauge(
    'database_connections',
    'Number of database connections',
    ['pool']
)


def setup_metrics(app: FastAPI) -> None:
    """配置Prometheus指标"""
    # 挂载metrics端点
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

