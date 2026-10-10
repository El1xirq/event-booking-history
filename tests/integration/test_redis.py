import asyncio

from app.utils.reservation_cache import (
    hold_seat, 
    get_held_by, 
    is_seat_held, 
    get_held_seat_ids,
    release_seat,
    )

async def test_hold_and_release(redis):
    """Test function redis"""
    assert await hold_seat(redis, "e", "s", "r1", ttl=10) is True
    assert await hold_seat(redis, "e", "s", "r1", ttl=10) is None
    assert await get_held_by(redis, "e", "s") == "r1"
    assert await is_seat_held(redis, "e", "s") is True
    assert await get_held_seat_ids(redis, "e") == {"s"}
    await release_seat(redis, "e", "s")
    assert await is_seat_held(redis, "e", "s") is False
    assert await get_held_by(redis, "e", "s") is None


async def test_hold_ttl_expires(redis):
    """TEST ttl redis"""
    assert await hold_seat(redis, "e", "s", "r1", ttl=1) is True
    await asyncio.sleep(2)
    assert await is_seat_held(redis, "e", "s") is False
    assert await get_held_by(redis, "e", "s") is None
