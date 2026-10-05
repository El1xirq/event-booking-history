from httpx import AsyncClient
import pytest

async def test_register_success(client: AsyncClient, session):
    """POST /auth/register creates user and returns token pair"""
    response = await client.post("/auth/register", json={
        "email": "newuser@test.com",
        "password": "secret123"
    })
    assert response.status_code==201
    body = response.json()
    assert "access_token" in body
    assert body["access_token"]

    assert "refresh_token" in response.cookies
    assert response.cookies["refresh_token"]


    from app.db.models.user import UserORM
    from sqlalchemy import select

    user = (await session.execute(select(UserORM).where(UserORM.email=="newuser@test.com"))).scalar_one_or_none()

    assert user is not None
    assert user.email == "newuser@test.com"
    assert user.is_active is True
    assert user.password_hash != "secret123"

    from app.db.models.refresh_token import RefreshTokenORM

    token = (await session.execute(
        select(RefreshTokenORM).where(RefreshTokenORM.user_id == user.id)
        )).scalar_one_or_none()
    assert token is not None
    assert token.revoked_at is None


async def test_register_duplicate_email(client: AsyncClient, session):
    """POST /auth/register creates user duplicate email exception 409"""
    response1 = await client.post("/auth/register", json={
        "email": "duplicate@example.com",
        "password": "secret123"
    })
    assert response1.status_code == 201

    from app.db.models.user import UserORM
    from sqlalchemy import select

    user = (await session.execute(select(UserORM).where(UserORM.email=="duplicate@example.com"))).scalar_one_or_none()

    assert user is not None
    assert user.email == "duplicate@example.com"
    assert user.is_active is True

    response2 = await client.post("/auth/register", json={
        "email": "duplicate@example.com",
        "password": "secret123"
    })

    assert response2.status_code == 409
    body = response2.json()
    assert body['error_code'] == 'CONFLICT'


async def test_register_invalid_email(client: AsyncClient):
    """POST /auth/register creates user invalid email"""
    response = await client.post("/auth/register", json={
        "email": "invalidemail",
        "password": "secret123"
    })
    assert response.status_code == 422


async def test_register_short_password(client: AsyncClient):
    """POST /auth/register creates user invalid password min_length 8"""
    response = await client.post("/auth/register", json={
        "email": "newuser@test.com",
        "password": "123"
    })
    assert response.status_code == 422


async def test_login_success(client: AsyncClient, registered_user):
    """POST /auth/login login user, 200 access + cookie(refresh)"""
    response = await client.post("/auth/login", json={
        "email": "test@test.com",
        "password": "secret123"
    })
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body['access_token']

    assert "refresh_token" in response.cookies
    assert response.cookies["refresh_token"]


async def test_login_wrong_password(client: AsyncClient, registered_user):
    """POST /auth/login login user, wrong password"""
    response = await client.post("/auth/login", json={
        "email": "test@test.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    body = response.json()
    assert body['error_code'] == "UNAUTHORIZED"


async def test_login_nonexistent_user(client: AsyncClient):
    """POST /auth/login login nonexsistent user"""
    response = await client.post("/auth/login", json={
        "email": "nonexsistent@example.com",
        "password": "secret123"
    })
    assert response.status_code == 401
    body = response.json()
    assert body['error_code'] == "UNAUTHORIZED"


async def test_login_inactive_user(client: AsyncClient, registered_user, session):
    """POST /auth/login is not active user, exception 403"""
    from sqlalchemy import update
    from app.db.models.user import UserORM
    await session.execute(update(UserORM).where(UserORM.email == "test@test.com").values(is_active = False))
    await session.commit()

    response = await client.post("/auth/login", json={
        "email": "test@test.com",
        "password": "secret123"
    })
    assert response.status_code == 403
    body = response.json()
    assert body['error_code'] == "FORBIDDEN"


async def test_me_success(client: AsyncClient, auth_tokens):
    """GET /auth/me is user, return info user"""
    response = await client.get("/auth/me", headers={
        "Authorization": f"Bearer {auth_tokens['access']}"
        })

    assert response.status_code == 200
    body = response.json()
    assert body['id']
    assert body['email'] == "test@test.com"
    assert body['role']
    assert body['is_active']


async def test_me_without_token(client: AsyncClient):
    """GET /auth/me without token in headers, exception 401"""
    response = await client.get("/auth/me")
    assert response.status_code == 401


async def test_me_invalid_token(client: AsyncClient):
    """GET /auth/me invalid token in headers, exception 401"""
    response = await client.get("/auth/me", headers={
        "Authorization": "Bearer invalidtoken"
    })
    assert response.status_code == 401
    body = response.json()
    assert body['error_code'] == "UNAUTHORIZED"


async def test_me_refresh_instead_of_access(client: AsyncClient, auth_tokens):
    """GET /auth/me refresh_token in headers, exception 401"""
    response = await client.get("/auth/me", headers={
        "Authorization": f"Bearer {auth_tokens['refresh']}"
    })
    assert response.status_code == 401
    body = response.json()
    assert body['error_code'] == "UNAUTHORIZED"


async def test_refresh_success(client: AsyncClient, auth_tokens):
    """POST /auth/refresh get access token and new refresh_token(cookie)"""
    response = await client.post("/auth/refresh", cookies={
        "refresh_token": auth_tokens["refresh"]
    })
    assert response.status_code == 200
    body = response.json()
    assert 'access_token' in body
    assert body['access_token']
    assert response.cookies["refresh_token"] != auth_tokens["refresh"]


async def test_refresh_reuse_revoked(client: AsyncClient, auth_tokens, session):
    """POST /auth/refresh test reuse revoked, exception 401"""
    response1 = await client.post("/auth/refresh", cookies={
        "refresh_token": auth_tokens["refresh"]
    })
    assert response1.status_code == 200
    body = response1.json()
    assert 'access_token' in body
    assert body['access_token']
    assert response1.cookies["refresh_token"] != auth_tokens["refresh"]


    response2 = await client.post("/auth/refresh", cookies={
        "refresh_token": auth_tokens["refresh"]
    })
    assert response2.status_code == 401
    data = response2.json()
    assert data['error_code'] == "UNAUTHORIZED"


    response3 = await client.post("/auth/refresh", cookies={
        "refresh_token": response1.cookies['refresh_token']
    })
    assert response3.status_code == 401

    from sqlalchemy import select
    from app.db.models.refresh_token import RefreshTokenORM
    from app.utils.security import hash_refresh_token

    refresh = (await session.execute(
        select(RefreshTokenORM).where(RefreshTokenORM.token_hash == hash_refresh_token(response1.cookies['refresh_token']))
        )).scalar_one_or_none()
    assert refresh is not None
    assert refresh.revoked_at is not None


async def test_refresh_without_cookie(client: AsyncClient):
    """POST /auth/refresh test get refresh token no cookie, exception 401"""
    response = await client.post("/auth/refresh")
    assert response.status_code == 401
    body = response.json()
    assert body['error_code'] == "UNAUTHORIZED"


async def test_refresh_garbage_token(client: AsyncClient):
    """POST /auth/refresh test get refresh token is invalid cookie token(NO JWT), exception 401"""
    response = await client.post("/auth/refresh", cookies={
        "refresh_token": "invalidtoken"
    })
    assert response.status_code == 401
    body = response.json()
    assert body['error_code'] == "UNAUTHORIZED"


async def test_logout_success(client: AsyncClient, session, auth_tokens):
    """POST /auth/logout logout user 204, cookie delete and refresh revoke"""
    response = await client.post("/auth/logout", cookies={
        "refresh_token": auth_tokens['refresh']
    })
    assert response.status_code == 204
    from sqlalchemy import select
    from app.db.models.refresh_token import RefreshTokenORM
    from app.utils.security import hash_refresh_token

    refresh = (await session.execute(
        select(RefreshTokenORM).where(RefreshTokenORM.token_hash == hash_refresh_token(auth_tokens['refresh']))
        )).scalar_one_or_none()
    assert refresh is not None
    assert refresh.revoked_at is not None


async def test_logout_without_cookie(client: AsyncClient):
    """POST /auth/logout logout user no cookie, 204"""
    response = await client.post("/auth/logout")
    assert response.status_code == 204 


async def test_refresh_after_logout(client: AsyncClient, auth_tokens, session):
    """POST /auth/logout test logout after refresh token, exception 401"""
    response1 = await client.post("/auth/logout", cookies={
        "refresh_token": auth_tokens['refresh']
    })
    assert response1.status_code == 204
    from sqlalchemy import select
    from app.db.models.refresh_token import RefreshTokenORM
    from app.utils.security import hash_refresh_token

    refresh = (await session.execute(
        select(RefreshTokenORM).where(RefreshTokenORM.token_hash == hash_refresh_token(auth_tokens['refresh']))
        )).scalar_one_or_none()
    assert refresh is not None
    assert refresh.revoked_at is not None

    response2 = await client.post("/auth/refresh", cookies={
        "refresh_token": auth_tokens['refresh']
    })
    assert response2.status_code == 401


