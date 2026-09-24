from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
import pytest

from app.core.config import settings
from app.core.exceptions.domain import InvalidTokenException
from app.db.models.enums import UserRole
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    get_password_hash,
    verify_password,
    hash_refresh_token,
)


def test_hash_password_is_not_plain():
    password = "secret123"
    hashed = get_password_hash(password)
    assert hashed != password
    assert len(hashed) > 20 


def test_hash_password_different_for_same_input():
    password = "secret123"
    h1 = get_password_hash(password)
    h2 = get_password_hash(password)
    assert h1 != h2


def test_verify_password_correct():
    password = "secret123"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed) is True


def test_verify_password_incorrect():
    password = "secret123"
    hashed = get_password_hash(password)
    assert verify_password("wrong", hashed) is False


def test_create_access_token_returns_string():
    token = create_access_token(uuid4(), UserRole.CUSTOMER, "test@test.com")
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_access_token_payload():
    user_id = uuid4()
    token = create_access_token(user_id, UserRole.CUSTOMER, "test@test.com")

    payload = jwt.decode(
        token, settings.secret_key, algorithms=[settings.algorithm]
    )

    assert payload["sub"] == str(user_id)
    assert payload["role"] == UserRole.CUSTOMER.value
    assert payload["email"] == "test@test.com"
    assert payload["type"] == "access"
    assert "exp" in payload


def test_verify_access_token_ok():
    user_id = uuid4()
    token = create_access_token(user_id, UserRole.CUSTOMER, "test@test.com")

    payload = verify_token(token, "access")

    assert payload["sub"] == str(user_id)
    assert payload["type"] == "access"


def test_create_refresh_token_returns_tuple():
    result = create_refresh_token(uuid4())
    assert isinstance(result, tuple)
    assert len(result) == 2

    token, expires_at = result
    assert isinstance(token, str)
    assert isinstance(expires_at, datetime)


def test_create_refresh_token_payload():
    user_id = uuid4()
    token, _ = create_refresh_token(user_id)

    payload = jwt.decode(
        token, settings.secret_key, algorithms=[settings.algorithm]
    )

    assert payload["sub"] == str(user_id)
    assert payload["type"] == "refresh"
    assert "exp" in payload


def test_create_refresh_token_expires_in_future():
    _, expires_at = create_refresh_token(uuid4())
    assert expires_at > datetime.now(timezone.utc)


def test_verify_refresh_as_access_raises():
    """Refresh нельзя использовать как access."""
    token, _ = create_refresh_token(uuid4())
    with pytest.raises(InvalidTokenException):
        verify_token(token, "access")


def test_verify_access_as_refresh_raises():
    """Access нельзя использовать как refresh."""
    token = create_access_token(uuid4(), UserRole.CUSTOMER, "test@test.com")
    with pytest.raises(InvalidTokenException):
        verify_token(token, "refresh")


def test_verify_expired_token_raises():
    """Токен с exp в прошлом → InvalidTokenException."""
    expired_payload = {
        "sub": str(uuid4()),
        "type": "access",
        "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
    }
    token = jwt.encode(
        expired_payload, settings.secret_key, algorithm=settings.algorithm
    )

    with pytest.raises(InvalidTokenException):
        verify_token(token, "access")


def test_verify_tampered_token_raises():
    """Токен, подписанный другим ключом, → InvalidTokenException."""
    payload = {
        "sub": str(uuid4()),
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
    }
    token = jwt.encode(payload, "wrong-secret-key", algorithm=settings.algorithm)

    with pytest.raises(InvalidTokenException):
        verify_token(token, "access")


def test_verify_garbage_token_raises():
    with pytest.raises(InvalidTokenException):
        verify_token("not-a-jwt", "access")


def test_hash_refresh_token_deterministic():
    token = "some-refresh-token"
    assert hash_refresh_token(token) == hash_refresh_token(token)


def test_hash_refresh_token_length():
    """sha256 hex → 64 символа."""
    assert len(hash_refresh_token("any")) == 64


def test_hash_refresh_token_different_inputs():
    assert hash_refresh_token("a") != hash_refresh_token("b")