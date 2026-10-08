from httpx import AsyncClient
from sqlalchemy import select, func
from uuid import UUID

from app.db.models.seat import SeatORM

async def test_create_seat_success(client: AsyncClient, session, organizer_tokens, venue):
    """POST /venues/{venue}/seats create seats, organizer"""
    for row, num in [("1", "1"), ("1", "2"), ("2", "1")]:
        response = await client.post(
            f"/venues/{venue}/seats",
            headers={"Authorization": f"Bearer {organizer_tokens['access']}"},
            json={"row_number": row, "seat_number": num, "seat_type": "standard"}
            )
        assert response.status_code == 201
    count = (
        await session.execute(
            select(func.count())
            .select_from(SeatORM)
            .where(SeatORM.venue_id == UUID(venue))
        )
    ).scalar_one()
    assert count == 3


async def test_create_seat_duplicate(client: AsyncClient, organizer_tokens, venue):
    """POST /venues/{venue}/seats create duplicate seat, exception 409"""
    response1 = await client.post(
        f"/venues/{venue}/seats",
        headers={"Authorization": f"Bearer {organizer_tokens['access']}"},
        json={"row_number": "1", "seat_number": "1", "seat_type": "standard"}
        )
    assert response1.status_code == 201

    response2 = await client.post(
        f"/venues/{venue}/seats",
        headers={"Authorization": f"Bearer {organizer_tokens['access']}"},
        json={"row_number": "1", "seat_number": "1", "seat_type": "standard"}
        )
    assert response2.status_code == 409


async def test_create_seat_in_foreign_venue(client: AsyncClient, another_organizer_tokens, venue):
    """POST /venues/{venue}/seats create seat another organizer, exception 403"""
    response = await client.post(
        f"/venues/{venue}/seats",
        headers={"Authorization": f"Bearer {another_organizer_tokens['access']}"},
        json={"row_number": "1", "seat_number": "1", "seat_type": "standard"},
        )
    assert response.status_code == 403


async def test_get_seats_by_venue(client: AsyncClient, seats, venue):
    """GET /venues/{venue}/seats get seats by venue"""
    response = await client.get(f"/venues/{venue}/seats")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 3


async def test_delete_seat_success(client, session, organizer_tokens, venue):
    """DELETE /venues/{venue}/seats/{seat_id} deletes seat."""
    create = await client.post(
        f"/venues/{venue}/seats",
        headers={"Authorization": f"Bearer {organizer_tokens['access']}"},
        json={"row_number": "9", "seat_number": "9", "seat_type": "standard"},
    )
    assert create.status_code == 201
    seat_id = create.json()["id"]

    delete = await client.delete(
        f"/venues/{venue}/seats/{seat_id}",
        headers={"Authorization": f"Bearer {organizer_tokens['access']}"},
    )
    assert delete.status_code == 204

    seat = (
        await session.execute(select(SeatORM).where(SeatORM.id == seat_id))
    ).scalar_one_or_none()
    assert seat is None