"""
OpenTelemetry tracing setup
"""
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from fastapi import FastAPI

from app.core.config import settings


def setup_tracing(app: FastAPI) -> None:
    """配置OpenTelemetry追踪"""
    
    if not settings.JAEGER_ENABLED:
        return
    
    # 创建Resource
    resource = Resource.create({
        "service.name": settings.APP_NAME,
        "service.version": settings.VERSION,
        "deployment.environment": settings.ENVIRONMENT
    })
    
    # 创建TracerProvider
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)
    
    # 配置Jaeger Exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name=settings.JAEGER_HOST,
        agent_port=settings.JAEGER_PORT,
    )
    
    # 添加Span Processor
    provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
    
    # 自动instrumentation
    FastAPIInstrumentor.instrument_app(app)


def get_tracer(name: str = __name__):
    """获取tracer实例"""
    return trace.get_tracer(name)

