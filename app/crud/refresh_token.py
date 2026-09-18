from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, update

from app.db.session import SessionDep
from app.db.models.refresh_token import RefreshTokenORM
from app.core.exceptions.domain import DatabaseException




async def save_refresh_token(
    user_id: UUID,
    token_hash: str,
    expires_at: datetime,
    session: SessionDep,
) -> RefreshTokenORM:
    """Saves the refresh token in the database"""
    record = RefreshTokenORM(user_id=user_id,token_hash=token_hash, expires_at=expires_at)
    try:
        session.add(record)
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        raise DatabaseException()

    await session.refresh(record)
    return record


async def get_refresh_by_hash(token_hash: str, session: SessionDep) -> RefreshTokenORM | None:
    """Get refresh by hash or None"""
    stmt = select(RefreshTokenORM).where(RefreshTokenORM.token_hash == token_hash)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def revoke_refresh_token(record: RefreshTokenORM,session: SessionDep) -> None:
    """Revoke refresh token"""
    try:
        record.revoked_at = datetime.now(timezone.utc)
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        raise DatabaseException()


async def revoke_all_user_tokens(user_id: UUID, session: SessionDep) -> None:
    """Massively revokes all active user tokens"""
    stmt = (update(RefreshTokenORM)
            .where(RefreshTokenORM.user_id == user_id, RefreshTokenORM.revoked_at.is_(None))
            .values(revoked_at=datetime.now(timezone.utc)))
    try: 
        await session.execute(stmt)
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        raise DatabaseException()
