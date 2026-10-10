from typing import Annotated, AsyncIterator
from fastapi import Depends
from redis.asyncio import ConnectionPool, Redis
from app.core.config import settings


redis_pool = ConnectionPool.from_url(
    settings.redis_url,
    decode_responses=True,
)


async def get_redis() -> AsyncIterator[Redis]:
    client = Redis(connection_pool=redis_pool)
    try:
        yield client
    finally:
        await client.aclose()


RedisDep = Annotated[Redis, Depends(get_redis)]

