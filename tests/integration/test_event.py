from httpx import AsyncClient
from sqlalchemy import select, func
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.db.models.event import EventORM
from app.db.models.event_seat import EventSeatORM

async def test_create_event_success(client: AsyncClient, venue, seats, session, organizer_tokens):
    """POST /events create event, seat organizer"""
    starts = datetime.now(timezone.utc) + timedelta(days=7)
    ends = starts + timedelta(hours=2)

    response = await client.post(
        "/events",
        headers={"Authorization": f"Bearer {organizer_tokens['access']}"},
        json={
            "title": "Test Event",
            "description": "Test",
            "venue_id": venue,
            "starts_at": starts.isoformat(),
            "ends_at": ends.isoformat(),
            "standard_price": "1000.00",
            "vip_price": "3000.00",
        },
    )

    assert response.status_code == 201
    body = response.json()

    event = (await session.execute(
        select(EventORM).where(EventORM.id == body['id']))
        ).scalar_one_or_none()
    assert event is not None
    assert event.title == body['title']
    assert str(event.id) == body["id"]

    count = (
        await session.execute(
            select(func.count())
            .select_from(EventSeatORM)
            .where(EventSeatORM.event_id == event.id)
        )
    ).scalar_one()

    assert count == len(seats)


async def test_create_event_customer_forbidden(client: AsyncClient, auth_tokens, venue):
    """POST /events create event customer role, exception 403"""
    starts = datetime.now(timezone.utc) + timedelta(days=7)
    ends = starts + timedelta(hours=2)

    response = await client.post(
        "/events",
        headers={"Authorization": f"Bearer {auth_tokens['access']}"},
        json={
            "title": "Test Event",
            "description": "Test",
            "venue_id": venue,
            "starts_at": starts.isoformat(),
            "ends_at": ends.isoformat(),
            "standard_price": "1000.00",
            "vip_price": "3000.00",
        },
    )
    assert response.status_code == 403
    body = response.json()
    assert body['error_code'] == "FORBIDDEN"


async def test_create_event_in_foreign_venue(client: AsyncClient, venue, another_organizer_tokens):
    """POST /events create event not owner venue, exception 403"""
    starts = datetime.now(timezone.utc) + timedelta(days=7)
    ends = starts + timedelta(hours=2)

    response = await client.post(
        "/events",
        headers={"Authorization": f"Bearer {another_organizer_tokens['access']}"},
        json={
            "title": "Test Event",
            "description": "Test",
            "venue_id": venue,
            "starts_at": starts.isoformat(),
            "ends_at": ends.isoformat(),
            "standard_price": "1000.00",
            "vip_price": "3000.00",
        },
    )
    assert response.status_code == 403
    body = response.json()
    assert body['error_code'] == "FORBIDDEN"


async def test_create_event_nonexistent_venue(client: AsyncClient, organizer_tokens):
    """POST /events create event nonexsistent venue, exception 404"""
    starts = datetime.now(timezone.utc) + timedelta(days=7)
    ends = starts + timedelta(hours=2)

    response = await client.post(
        "/events",
        headers={"Authorization": f"Bearer {organizer_tokens['access']}"},
        json={
            "title": "Test Event",
            "description": "Test",
            "venue_id": str(uuid4()),
            "starts_at": starts.isoformat(),
            "ends_at": ends.isoformat(),
            "standard_price": "1000.00",
            "vip_price": "3000.00",
        },
    )
    assert response.status_code == 404


async def test_get_events_list(client: AsyncClient, venue, organizer_tokens):
    """GET /events get list events"""
    starts1 = datetime.now(timezone.utc) + timedelta(days=7)
    ends1 = starts1 + timedelta(hours=2)
    response1 = await client.post(
        "/events",
        headers={"Authorization": f"Bearer {organizer_tokens['access']}"},
        json={
            "title": "Test Event1",
            "description": "Test",
            "venue_id": venue,
            "starts_at": starts1.isoformat(),
            "ends_at": ends1.isoformat(),
            "standard_price": "1000.00",
            "vip_price": "3000.00",
        },
    )
    assert response1.status_code == 201

    starts2 = datetime.now(timezone.utc) + timedelta(days=5)
    ends2 = starts2 + timedelta(hours=2)
    response2 = await client.post(
        "/events",
        headers={"Authorization": f"Bearer {organizer_tokens['access']}"},
        json={
            "title": "Test Event2",
            "description": "Test",
            "venue_id": venue,
            "starts_at": starts2.isoformat(),
            "ends_at": ends2.isoformat(),
            "standard_price": "1000.00",
            "vip_price": "3000.00",
        },
    )
    assert response2.status_code == 201

    response = await client.get("/events")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]['title'] == "Test Event1"
    assert body[1]['title'] == "Test Event2"


async def test_get_event_by_id_not_found(client: AsyncClient):
    """GET /events/{event_id} search event not created, exception 404"""
    response = await client.get(f"/events{str(uuid4())}")
    assert response.status_code == 404


async def test_update_event_not_owner(client: AsyncClient, another_organizer_tokens, event):
    """PATCH /events/{event_id} patch event not owner, exception 403"""
    response = await client.patch(
        f"/events/{event}",
        headers={"Authorization": f"Bearer {another_organizer_tokens['access']}"},
        json={'title': 'Updated'}
        )
    assert response.status_code == 403
    body = response.json()
    assert body['error_code'] == "FORBIDDEN"


async def test_delete_venue_with_events(client: AsyncClient, event, venue, organizer_tokens):
    """DELETE /venue/{venue_id} delete venue with events, exception 409"""
    response = await client.delete(
        f"/venues/{venue}",
        headers={"Authorization": f"Bearer {organizer_tokens['access']}"}
        )
    assert response.status_code == 409
