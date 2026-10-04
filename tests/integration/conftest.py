import pytest_asyncio

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