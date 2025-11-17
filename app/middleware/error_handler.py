"""
Error handler middleware
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import AppException

import structlog

logger = structlog.get_logger(__name__)

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """错误处理中间件"""
    
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
            
        except AppException as e:
            logger.error(
                "app_exception",
                exception=e,
                request=request,
                exc_info=True,
            )
            # 业务异常
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "code": e.code,
                    "message": e.message,
                    "details": e.details,
                }
            )
        except Exception as e:
            logger.error(
                "unexpected_exception",
                exception=e,
                request=request,
                exc_info=True,
            )
            # 未预期的异常
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "code": "INTERNAL_ERROR",
                    "message": "An internal error occurred",
                    "details": str(e) if request.app.debug else None,
                }
            )

