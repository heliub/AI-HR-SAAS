"""
FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.v1.router import api_router
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.observability.logging.middleware import LoggingMiddleware
from app.observability.tracing.middleware import TraceMiddleware
from app.observability.metrics.setup import setup_metrics
from app.observability.metrics.middleware import MetricsMiddleware
import os
from app.init_app import init_app, close_app


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    await init_app(app)
    yield
    await close_app(app)


def create_application() -> FastAPI:
    """创建FastAPI应用"""
    os.environ["VOLCENGINE_API_KEY"] = settings.VOLCENGINE_API_KEY
    os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        description="AI-Powered HR Recruitment SAAS Platform",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )
    
    # CORS配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境应配置具体域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 添加中间件（注意顺序）
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(LoggingMiddleware)
    # app.add_middleware(MetricsMiddleware)
    app.add_middleware(TraceMiddleware)  # 轻量级trace中间件
    # app.add_middleware(TenantContextMiddleware)
    
    # 配置指标
    setup_metrics(app)
    
    # 注册路由
    app.include_router(api_router, prefix="/api/v1")
    
    # 健康检查
    @app.get("/health")
    async def health_check():
        return JSONResponse(
            content={
                "status": "healthy",
                "service": settings.APP_NAME,
                "version": settings.VERSION,
            }
        )
    
    return app


app = create_application()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )

