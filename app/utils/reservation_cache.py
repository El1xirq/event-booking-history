from redis.asyncio import Redis
from uuid import UUID

async def hold_seat(
        redis: Redis, 
        event_id: UUID, 
        seat_id: UUID, 
        reservation_id: UUID, 
        ttl: int
        ) -> bool:
    """Create redis hold seat"""
    key = f"seat:{event_id}:{seat_id}"
    return await redis.set(key, value=str(reservation_id), ex=ttl, nx=True)


async def release_seat(redis: Redis, event_id: UUID, seat_id: UUID) -> None:
    """Delete seat"""
    key = f"seat:{event_id}:{seat_id}"
    await redis.delete(key)


async def is_seat_held(redis: Redis, event_id: UUID, seat_id: UUID) -> bool:
    """EXISTS seat True/False"""
    key = f"seat:{event_id}:{seat_id}"
    return bool(await redis.exists(key))


async def get_held_by(redis: Redis, event_id: UUID, seat_id: UUID) -> str | None:
    """GET value for redis"""
    key = f"seat:{event_id}:{seat_id}"
    return await redis.get(key)


async def get_held_seat_ids(redis: Redis, event_id: UUID) -> set[str]:
    """Get all held seat ids for an event."""
    pattern = f"seat:{event_id}:*"
    result: set[str] = set()
    async for key in redis.scan_iter(match=pattern):
        seat_id = key.split(":")[-1]
        result.add(seat_id)
    return result








