"""
Redis client management
"""
from typing import Optional
import json

from redis.asyncio import Redis, ConnectionPool

from app.core.config import settings

# 全局Redis实例
redis_client: Optional[Redis] = None
redis_pool: Optional[ConnectionPool] = None


async def init_redis() -> None:
    """初始化Redis连接"""
    global redis_client, redis_pool
    
    redis_pool = ConnectionPool.from_url(
        settings.REDIS_URL,
        max_connections=settings.REDIS_MAX_CONNECTIONS,
        decode_responses=True,
    )
    
    redis_client = Redis(connection_pool=redis_pool)


async def close_redis() -> None:
    """关闭Redis连接"""
    global redis_client, redis_pool
    
    if redis_client:
        await redis_client.close()
    
    if redis_pool:
        await redis_pool.disconnect()


def get_redis() -> Redis:
    """获取Redis客户端"""
    if redis_client is None:
        raise RuntimeError("Redis client not initialized")
    return redis_client


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, redis: Redis):
        self.redis = redis
    
    async def get(self, key: str) -> Optional[any]:
        """获取缓存"""
        value = await self.redis.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
    
    async def set(
        self, 
        key: str, 
        value: any, 
        ttl: int = 3600
    ) -> None:
        """设置缓存"""
        if isinstance(value, (dict, list)):
            value = json.dumps(value, default=str)
        
        await self.redis.setex(key, ttl, value)
    
    async def delete(self, key: str) -> None:
        """删除缓存"""
        await self.redis.delete(key)
    
    async def delete_pattern(self, pattern: str) -> None:
        """删除匹配模式的缓存"""
        keys = []
        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)
        
        if keys:
            await self.redis.delete(*keys)
    
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        return await self.redis.exists(key) > 0
    
    async def ttl(self, key: str) -> int:
        """获取缓存剩余时间"""
        return await self.redis.ttl(key)
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """递增计数器"""
        return await self.redis.incrby(key, amount)
    
    async def decr(self, key: str, amount: int = 1) -> int:
        """递减计数器"""
        return await self.redis.decrby(key, amount)


def get_cache_manager() -> CacheManager:
    """获取缓存管理器实例"""
    return CacheManager(get_redis())

