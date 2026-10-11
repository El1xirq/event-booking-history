from datetime import datetime, timedelta, timezone
from uuid import uuid4, UUID
from decimal import Decimal
from sqlalchemy import update, select, or_, insert
from sqlalchemy.exc import SQLAlchemyError
from redis.asyncio import Redis

from app.utils.reservation_cache import (
    hold_seat, 
    save_reservation_map, 
    release_seat,
    get_reservation_map,
    get_held_by,
    delete_reservation_map)
from app.db.models.reservation import ReservationORM
from app.db.models.event_seat import EventSeatORM
from app.db.models.enums import ReservationStatus
from app.db.session import SessionDep
from app.core.exceptions.domain import ConflictException, DatabaseException, NotFoundException
from app.core.config import settings
from app.db.models.enums import ReservationStatus
from app.db.models.user import UserORM


async def get_reservation_by_id(reservation_id: UUID, session: SessionDep) -> ReservationORM:
    """Get reservation by id"""
    stmt = select(ReservationORM).where(ReservationORM.id == reservation_id)
    result = (await session.execute(stmt)).scalar_one_or_none()
    if result is None:
        raise NotFoundException()
    return result


async def create_reservation(
    event_id: UUID,
    event_seat_id: UUID,
    redis: Redis,
    user: UserORM,
) -> UUID:
    """Atomically reserves a seat for 15 minutes"""
    reservation_id = uuid4()
    res = await hold_seat(redis, event_id, event_seat_id, reservation_id, settings.hold_ttl_seconds)
    if res is None:
        raise ConflictException("This reservation is already taken")
    res1 = await save_reservation_map(redis, user.id, reservation_id, event_id, event_seat_id, settings.hold_ttl_seconds)
    if res1 is None:
        await release_seat(redis, event_id, event_seat_id)
        raise DatabaseException()
    return reservation_id
 

async def confirm_reservation(
        reservation_id: UUID,
        user_id: UUID,
        session: SessionDep,
        redis: Redis) -> ReservationORM:
    """Confirm pending reservation"""
    reservation = await get_reservation_map(redis, reservation_id)
    if reservation is None:
        raise NotFoundException("Reservation not found")
    if reservation['user_id'] != str(user_id):
        raise NotFoundException("Reservation not found")

    event_seat = await get_held_by(redis, reservation['event_id'], reservation['seat_id'])
    if event_seat is None:
        raise ConflictException("This reservation is taken or expired")
    

    reservation_new = ReservationORM(
        id=reservation_id, 
        user_id=UUID(reservation['user_id']), 
        event_id=UUID(reservation['event_id']), 
        status=ReservationStatus.CONFIRMED)
    
    stmt_event_seat = (update(EventSeatORM)
                       .where(EventSeatORM.id == UUID(reservation["seat_id"]))
                       .values(hold_expires_at = None, reservation_id=reservation_id))
    try:
        session.add(reservation_new)
        result = await session.execute(stmt_event_seat)
        if result.rowcount == 0:
            await session.rollback()
            raise DatabaseException()
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        raise DatabaseException()

    await release_seat(redis, reservation['event_id'], reservation['seat_id'])
    await delete_reservation_map(redis, reservation_id)
    await session.refresh(reservation_new)
    return reservation_new


async def cancel_reservation(reservation_id: UUID, user_id: UUID, session: SessionDep, redis: Redis) -> None:
    """Cancel reservation"""
    reservation_map = await get_reservation_map(redis, reservation_id)
    if reservation_map is not None:
        if reservation_map['user_id'] != str(user_id):
            raise NotFoundException("Reservation not found")
        await release_seat(redis, reservation_map['event_id'], reservation_map['seat_id']) 
        await delete_reservation_map(redis, reservation_id)
        return None

    stmt = select(ReservationORM).where(ReservationORM.id == reservation_id)
    reservation = (await session.execute(stmt)).scalar_one_or_none()
    if reservation is None:
        raise NotFoundException("Reservation not found")
    if reservation.user_id != user_id:
        raise NotFoundException("Reservation not found")
    if reservation.status == ReservationStatus.CANCELLED:
        raise ConflictException('Reservation already cancelled')
    
    stmt2 = update(ReservationORM).where(ReservationORM.id == reservation_id).values(status=ReservationStatus.CANCELLED)
    stmt_event_seat = (update(EventSeatORM)
                       .where(EventSeatORM.reservation_id == reservation_id)
                       .values(reservation_id=None, hold_expires_at=None))
    try:
        await session.execute(stmt2)
        result = await session.execute(stmt_event_seat)
        if result.rowcount == 0:
            await session.rollback()
            raise DatabaseException()
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        raise DatabaseException()
    


async def get_user_reservations(user_id: UUID, session: SessionDep) -> list[ReservationORM]:
    """Get all user reservations"""
    stmt = select(ReservationORM).where(ReservationORM.user_id == user_id).order_by(ReservationORM.created_at.desc())
    result = (await session.execute(stmt)).scalars().all()
    return list(result)

