from httpx import AsyncClient
from sqlalchemy import select
from uuid import UUID, uuid4
import asyncio

from app.utils.reservation_cache import get_held_by, get_reservation_map, is_seat_held
from app.db.models.reservation import ReservationORM
from app.db.models.event_seat import EventSeatORM

async def test_create_reservation_success(client: AsyncClient, event, event_seat, redis, auth_tokens):
    """POST /reservations create reservation"""
    response = await client.post(
        "/reservations",
        headers={"Authorization": f"Bearer {auth_tokens['access']}"},
        json={"event_id": event, "event_seat_id": event_seat}
        )
    assert response.status_code == 201
    body = response.json()
    assert body['event_id'] == str(event)
    assert body['status'] == 'pending'

    assert await get_held_by(redis, event, event_seat) == body['id']
    reservation = await get_reservation_map(redis, body['id'])
    assert reservation["seat_id"] == str(event_seat)
    assert reservation["user_id"] == body["user_id"]
    assert reservation["event_id"] == str(event)



async def test_create_reservation_seat_taken(client: AsyncClient, auth_tokens, event_seat, event):
    """POST /reservations create busy reservaton, exception 409"""
    response1 = await client.post(
        "/reservations",
        headers={"Authorization": f"Bearer {auth_tokens['access']}"},
        json={"event_id": event, "event_seat_id": event_seat}
        )
    assert response1.status_code == 201

    response2 = await client.post(
        "/reservations",
        headers={"Authorization": f"Bearer {auth_tokens['access']}"},
        json={"event_id": event, "event_seat_id": event_seat}
        )
    assert response2.status_code == 409


async def test_create_reservation_nonexistent_seat(client: AsyncClient, auth_tokens, event):
    """POST /reservations create nonexsistent seat, exception 404"""
    response = await client.post(
        "/reservations",
        headers={"Authorization": f"Bearer {auth_tokens['access']}"},
        json={"event_id": event, "event_seat_id": str(uuid4())}
    )
    assert response.status_code == 404


async def test_confirm_reservation(client: AsyncClient, auth_tokens, reservation, session, redis, event_seat):
    """PATCH /reservations/{reservation_id}/confirm confirm reservation"""
    response = await client.patch(
        f"/reservations/{reservation}/confirm",
        headers={"Authorization": f"Bearer {auth_tokens['access']}"},
        )
    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'confirmed'

    rvn = (await session.execute(
        select(ReservationORM).where(ReservationORM.id == reservation))
        ).scalar_one_or_none()
    assert rvn is not None
    assert rvn.status == 'confirmed'

    assert await is_seat_held(redis, body['event_id'], event_seat) is False
    assert await get_reservation_map(redis, body['id']) is None
    

async def test_cancel_reservation_confirmed(client: AsyncClient, auth_tokens, reservation, event_seat, session):
    """DELETE /reservations/{reservation_id} cancel confirmed reservation"""
    response1 = await client.patch(
    f"/reservations/{reservation}/confirm",
    headers={"Authorization": f"Bearer {auth_tokens['access']}"},
    )
    assert response1.status_code == 200

    response = await client.delete(
        f"/reservations/{reservation}",
        headers={"Authorization": f"Bearer {auth_tokens['access']}"}
    )
    assert response.status_code == 204

    eseat = (await session.execute(
        select(EventSeatORM).where(EventSeatORM.id == UUID(event_seat)))
    ).scalar_one_or_none()
    assert eseat is not None
    assert eseat.reservation_id is None


async def test_cancel_reservation_pending(client: AsyncClient, auth_tokens, reservation, event_seat, redis, event):
    """DELETE /reservations/{reservation_id} cancel confirmed reservation"""
    response = await client.delete(
        f"/reservations/{reservation}",
        headers={"Authorization": f"Bearer {auth_tokens['access']}"}
    )
    assert response.status_code == 204
    assert await is_seat_held(redis, event, event_seat) is False


async def test_confirm_other_user_reservation(client: AsyncClient, another_customer_tokens, reservation):
    """PATCH /reservations/{reservation_id}/confirm confirm other user reservation, exception 404"""
    response = await client.patch(
        f"/reservations/{reservation}/confirm",
        headers={"Authorization": f"Bearer {another_customer_tokens['access']}"}
    )
    assert response.status_code == 404


async def test_concurrent_reservations(
        client: AsyncClient, 
        event, 
        event_seat, 
        session, 
        auth_tokens, 
        another_customer_tokens,
        redis):
    """POST /reservations create concurrent reservation, exception 409"""
    async def coro_a():
        response1 = await client.post(
            "/reservations",
            headers={"Authorization": f"Bearer {auth_tokens['access']}"},
            json={"event_id": event, "event_seat_id": event_seat},
            )
        return response1
    async def coro_b():
        response2 = await client.post(
            "/reservations",
            headers={"Authorization": f"Bearer {another_customer_tokens['access']}"},
            json={"event_id": event, "event_seat_id": event_seat},
            )
        return response2

    resp_a, resp_b = await asyncio.gather(coro_a(), coro_b())
    statuses = sorted([resp_a.status_code, resp_b.status_code])
    assert statuses == [201, 409]
    success_resp = resp_a if resp_a.status_code == 201 else resp_b
    assert await is_seat_held(redis, event, event_seat) == True
    assert await get_held_by(redis, event, event_seat) == success_resp.json()['id']
