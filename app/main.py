from fastapi import FastAPI
from contextlib import asynccontextmanager
from redis.asyncio import Redis

from app.core.logging import setup_logging
from app.db.redis import redis_pool
from app.api import health, auth, venue, event, seats, reservation
from app.core.exceptions.base import AppException
from app.core.exceptions.handlers import (RequestValidationError, 
                                          validation_exception_handler, 
                                          app_exception_handler, 
                                          global_exception_handler)

logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    client = Redis(connection_pool=redis_pool)
    try:
        await client.ping()
        logger.info("Redis connected")
    except Exception as e:
        logger.error(f"Redis error: {e}")
        raise
    finally:
        await client.aclose()
    yield
    await redis_pool.aclose()

app = FastAPI(lifespan=lifespan)

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(venue.router)
app.include_router(event.router)
app.include_router(seats.router)
app.include_router(reservation.router)