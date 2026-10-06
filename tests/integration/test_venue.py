from httpx import AsyncClient
from sqlalchemy import select
from uuid import uuid4

from app.db.models.venue import VenueORM


async def test_create_venue_success(client: AsyncClient, session, organizer_tokens):
    """POST /venues create venue organizer"""
    response = await client.post(
        "/venues",
        headers={"Authorization": f"Bearer {organizer_tokens['access']}"},
        json={
            "name": "Test Venue",
            "address": "Test Address 1",
            "description": "Test",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body['name'] == "Test Venue"

    venue = (await session.execute(
        select(VenueORM).where(VenueORM.id == body['id']))
        ).scalar_one_or_none()

    assert venue is not None
    assert venue.name == "Test Venue"


async def test_create_venue_customer_forbidden(client: AsyncClient, auth_tokens):
    """POST /venues create venue customer, exception 403"""
    response = await client.post(
            "/venues",
            headers={"Authorization": f"Bearer {auth_tokens['access']}"},
            json={
                "name": "Test Venue",
                "address": "Test Address 1",
                "description": "Test",
            },
        )

    assert response.status_code == 403
    body = response.json()
    assert body['error_code'] == "FORBIDDEN"


async def test_create_venue_unauthenticated(client: AsyncClient):
    """POST /venues create venue unautheticated(no tokens), exception 401"""
    response = await client.post(
            "/venues",
            json={
                "name": "Test Venue",
                "address": "Test Address 1",
                "description": "Test",
            },
        )

    assert response.status_code == 401


async def test_get_venues_list(client: AsyncClient, organizer_tokens):
    """GET /venues get venues list"""
    response1 = await client.post(
            "/venues",
            headers={"Authorization": f"Bearer {organizer_tokens['access']}"},
            json={
                "name": "Test Venue1",
                "address": "Test Address 1",
                "description": "Test",
            },
        )
    assert response1.status_code == 201

    response2 = await client.post(
            "/venues",
            headers={"Authorization": f"Bearer {organizer_tokens['access']}"},
            json={
                "name": "Test Venue2",
                "address": "Test Address 2",
                "description": "Test",
            },
        )
    assert response2.status_code == 201

    response3 = await client.post(
            "/venues",
            headers={"Authorization": f"Bearer {organizer_tokens['access']}"},
            json={
                "name": "Test Venue3",
                "address": "Test Address 3",
                "description": "Test",
            },
        )
    assert response3.status_code == 201


    response = await client.get("/venues")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 3
    assert body[0]['name'] == "Test Venue1"
    assert body[1]['name'] == "Test Venue2"
    assert body[2]['name'] == "Test Venue3"
    

async def test_get_venue_by_id_success(client: AsyncClient, venue):
    """GET /venues/{venue_id} search venue by id"""
    response = await client.get(f"/venues/{venue}")
    assert response.status_code == 200
    body = response.json()
    assert body['id'] == venue
    assert body['name'] == "Test Venue"


async def test_get_venue_by_id_not_found(client: AsyncClient):
    """GET /venues/{venue_id} search venue not created, exception 404"""
    response = await client.get(f"/venues/{uuid4()}")
    assert response.status_code == 404


async def test_update_venue_success(client: AsyncClient, venue, organizer_tokens, session):
    """PATCH /venues/{venue_id} patch venue, owner"""
    response = await client.patch(
        f"/venues/{venue}",
        headers={"Authorization": f"Bearer {organizer_tokens['access']}"},
        json={"name": "Updated"},
    )
    assert response.status_code == 200
    new_venue = (await session.execute(
        select(VenueORM).where(VenueORM.id == venue))
        ).scalar_one_or_none()
    
    assert new_venue is not None
    assert str(new_venue.id) == str(venue)


async def test_update_venue_not_owner(client: AsyncClient, venue, another_organizer_tokens):
    """PATCH /venues/{venue_id} patch venue not owner, exception 403"""
    response = await client.patch(
        f"/venues/{venue}",
        headers={"Authorization": f"Bearer {another_organizer_tokens['access']}"},
        json={"name": "Updated"},
    )
    assert response.status_code == 403
    body = response.json()
    assert body['error_code'] == "FORBIDDEN"


async def test_delete_venue_success(client: AsyncClient, venue, organizer_tokens, session):
    """DELETE /venues/venue{id} delete venue, owner"""
    response = await client.delete(
        f"/venues/{venue}",
        headers={"Authorization": f"Bearer {organizer_tokens['access']}"}
        )
    assert response.status_code == 204

    delete_venue = (await session.execute(
        select(VenueORM).where(VenueORM.id == venue))
        ).scalar_one_or_none()
    assert delete_venue is None


async def test_delete_venue_not_owner(client: AsyncClient, venue, another_organizer_tokens):
    """DELETE /venues/{venue_id} delete venue not owner, exception 403"""
    response = await client.delete(
        f"/venues/{venue}",
        headers={"Authorization": f"Bearer {another_organizer_tokens['access']}"}
    )
    assert response.status_code == 403