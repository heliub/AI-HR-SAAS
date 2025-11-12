from fastapi import FastAPI
from app.observability.instrumentation.database import setup_database_logging
from app.core.config import settings
from app.infrastructure.cache.redis import init_redis, close_redis
from app.infrastructure.database.session import init_db, close_db
from app.observability.logging.setup import setup_logging

async def init_app(app: FastAPI):
    setup_logging()
    await init_db()
    await init_redis()
    await init_database_logging()

async def close_app(app: FastAPI):
    await close_db()
    await close_redis()

async def init_database_logging():
    from app.infrastructure.database.session import engine
    setup_database_logging(
        engine,
        log_queries=settings.LOG_DATABASE_QUERIES,
        slow_query_threshold_ms=settings.SLOW_QUERY_THRESHOLD_MS
    )