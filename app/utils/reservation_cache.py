from redis.asyncio import Redis
from uuid import UUID
import json

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


async def save_reservation_map(
        redis: Redis,
        user_id: UUID, 
        reservation_id: UUID, 
        event_id: UUID, 
        seat_id: UUID, 
        ttl: int
        ) -> bool:
    """SET redis reservation"""
    key = f"reservation:{reservation_id}"
    value = {"event_id": str(event_id), "seat_id": str(seat_id), "user_id": str(user_id)}
    return await redis.set(key, value=json.dumps(value), ex=ttl)


async def get_reservation_map(redis: Redis, reservation_id: UUID) -> dict | None:
    """GET reservation value"""
    key = f"reservation:{reservation_id}"
    result = await redis.get(key)
    if result is None:
        return None
    return json.loads(result)


async def delete_reservation_map(redis: Redis, reservation_id: UUID) -> None:
    """DELETE reservation"""
    key = f"reservation:{reservation_id}"
    await redis.delete(key)







