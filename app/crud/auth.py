from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from uuid import UUID

from app.db.session import SessionDep
from app.db.models.user import UserORM
from app.schemas.auth_schema import UpdateUserSchema, RegistrationData
from app.core.exceptions.domain import NotFoundException, DatabaseException, ConflictException




async def get_user_by_id(user_id: UUID, session: SessionDep) -> UserORM:
    """Get user by id"""
    stmt = select(UserORM).where(UserORM.id == user_id, UserORM.is_active==True)
    result = (await session.execute(stmt)).scalar_one_or_none()
    if result is None:
        raise NotFoundException("User not found")
    return result
    

async def get_user_by_email(email: str, session: SessionDep) -> UserORM | None:
    """Get user by email"""
    stmt = select(UserORM).where(UserORM.email == email)
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_active_user_by_email(email: str, session: SessionDep) -> UserORM:
    """Get user by email is_active = True"""
    stmt = select(UserORM).where(UserORM.email == email, UserORM.is_active == True)
    user = (await session.execute(stmt)).scalar_one_or_none()
    if user is None:
        raise NotFoundException("User not found")
    return user
    

async def create_user(user: RegistrationData, session: SessionDep) -> UserORM:
    """Create user"""
    try:
        new_user = UserORM(email=user.email, hashed_password=user.hashed_password, role=user.role)
        session.add(new_user)
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise ConflictException("User with this email already exists")
    except SQLAlchemyError:
        await session.rollback()
        raise DatabaseException()
    
    await session.refresh(new_user)
    return new_user


async def update_user(user_id: UUID, user_update: UpdateUserSchema, session: SessionDep) -> UserORM:
    """Patch user"""
    user = await get_user_by_id(user_id, session)

    update_options = user_update.model_dump(exclude_none=True)
    
    if not update_options:
        return user

    try:
        stmt = update(UserORM).where(UserORM.id == user_id).values(update_options)
        await session.execute(stmt)
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        raise DatabaseException()

    return await get_user_by_id(user_id, session)

async def delete_user(user_id: UUID, session: SessionDep) -> bool:
    """Soft delete user"""
    stmt = (
        update(UserORM)
        .where(UserORM.id == user_id, UserORM.is_active == True)
        .values(is_active=False)
        .returning(UserORM.id)
    )
    try:
        result = await session.execute(stmt)
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        raise DatabaseException()

    if result.scalar_one_or_none() is None:
        raise NotFoundException("User not found")
    return True
    