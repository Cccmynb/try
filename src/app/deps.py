import os, asyncio
import redis.asyncio as redis
from app.db.base import AsyncSessionLocal

_redis: redis.Redis | None = None

async def get_db():
    async with AsyncSessionLocal() as s:
        yield s

async def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
    return _redis

# 简单令牌桶
async def rate_limit(r: redis.Redis, key: str, limit:int=10, window:int=60) -> bool:
    # 60s 内最多 10 次
    pipe = r.pipeline()
    pipe.incr(key)
    pipe.expire(key, window)
    cnt, _ = await pipe.execute()
    return int(cnt) <= limit
