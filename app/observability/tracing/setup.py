"""
OpenTelemetry tracing setup
"""
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from fastapi import FastAPI

from app.core.config import settings


def setup_tracing(app: FastAPI) -> None:
    """配置OpenTelemetry追踪"""
    
    # 创建Resource
    resource = Resource.create({
        "service.name": settings.APP_NAME,
        "service.version": settings.VERSION,
        "deployment.environment": settings.ENVIRONMENT
    })
    
    # 创建TracerProvider
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)
    
    if settings.JAEGER_ENABLED:
        # 配置OTLP Exporter
        otlp_exporter = OTLPSpanExporter(
            endpoint=settings.JAEGER_OTLP_ENDPOINT_HTTP
        )
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    else:
        # 配置控制台Exporter，用于本地调试
        console_exporter = ConsoleSpanExporter()
        provider.add_span_processor(BatchSpanProcessor(console_exporter))

    # 自动instrumentation
    FastAPIInstrumentor.instrument_app(app)


def get_tracer(name: str = __name__):
    """获取tracer实例"""
    return trace.get_tracer(name)

