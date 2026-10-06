import pytest_asyncio
from sqlalchemy import update

from app.db.models.user import UserORM
from app.db.models.enums import UserRole


@pytest_asyncio.fixture
async def registered_user(client):
    resp = await client.post("/auth/register", json={
        "email": "test@test.com",
        "password": "secret123",
    })
    return resp


@pytest_asyncio.fixture
async def auth_tokens(registered_user):
    access = registered_user.json()["access_token"]
    refresh = registered_user.cookies.get("refresh_token")
    return {"access": access, "refresh": refresh}


@pytest_asyncio.fixture
async def organizer_user(client, registered_user, session):
    await session.execute(
        update(UserORM).where(UserORM.email=="test@test.com").values(role='organizer')
        )
    await session.commit()
    response = await client.post("/auth/login", json={
        "email": "test@test.com",
        "password": "secret123",
    })
    return response


@pytest_asyncio.fixture
async def organizer_tokens(organizer_user):
    access = organizer_user.json()['access_token']
    refresh = organizer_user.cookies.get("refresh_token")
    return {"access": access, "refresh": refresh}


@pytest_asyncio.fixture
async def organizer_user(client, session):
    resp = await client.post("/auth/register", json={
        "email": "organizer@test.com",
        "password": "secret123",
    })
    assert resp.status_code == 201

    await session.execute(
        update(UserORM)
        .where(UserORM.email == "organizer@test.com")
        .values(role=UserRole.ORGANIZER.value)
    )
    await session.commit()


@pytest_asyncio.fixture
async def organizer_tokens(client, organizer_user):
    resp = await client.post("/auth/login", json={
        "email": "organizer@test.com",
        "password": "secret123",
    })
    assert resp.status_code == 200
    return {
        "access": resp.json()["access_token"],
        "refresh": resp.cookies.get("refresh_token"),
    }


@pytest_asyncio.fixture
async def another_organizer_tokens(client, session):
    """Register user and promote to organizer."""
    resp = await client.post("/auth/register", json={
        "email": "organizer_another@test.com",
        "password": "secret123",
    })
    assert resp.status_code == 201

    await session.execute(
        update(UserORM)
        .where(UserORM.email == "organizer_another@test.com")
        .values(role=UserRole.ORGANIZER.value)
    )
    await session.commit()

    return {
        "access": resp.json()["access_token"],
        "refresh": resp.cookies.get("refresh_token"),
    }


@pytest_asyncio.fixture
async def venue(client, organizer_tokens):
    resp = await client.post(
        "/venues",
        headers={"Authorization": f"Bearer {organizer_tokens['access']}"},
        json={
            "name": "Test Venue",
            "address": "Test Address 1",
            "description": "Test",
        },
    )
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest_asyncio.fixture
async def seats(client, organizer_tokens, venue):
    ids = []
    for row, num in [("1", "1"), ("1", "2"), ("2", "1")]:
        resp = await client.post(
            f"/venues/{venue}/seats",
            headers={"Authorization": f"Bearer {organizer_tokens['access']}"},
            json={"row_number": row, "seat_number": num, "seat_type": "standard"},
        )
        assert resp.status_code == 201
        ids.append(resp.json()["id"])
    return ids


@pytest_asyncio.fixture
async def event(client, organizer_tokens, venue, seats):
    from datetime import datetime, timedelta, timezone

    starts = datetime.now(timezone.utc) + timedelta(days=7)
    ends = starts + timedelta(hours=2)

    resp = await client.post(
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
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest_asyncio.fixture
async def event_seat(client, event):
    resp = await client.get(f"/events/{event}/seats")
    assert resp.status_code == 200
    seats = resp.json()
    assert len(seats) > 0
    return seats[0]["id"]