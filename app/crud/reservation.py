from datetime import datetime, timedelta, timezone
from uuid import uuid4, UUID
from decimal import Decimal
from sqlalchemy import update, select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.db.models.reservation import ReservationORM
from app.db.models.event_seat import EventSeatORM
from app.db.models.enums import ReservationStatus
from app.db.session import SessionDep
from app.core.exceptions.domain import ConflictException, DatabaseException, NotFoundException


async def get_reservation_by_id(reservation_id: UUID, session: SessionDep) -> ReservationORM:
    """Get reservation by id"""
    stmt = select(ReservationORM).where(ReservationORM.id == reservation_id)
    result = (await session.execute(stmt)).scalar_one_or_none()
    if result is None:
        raise NotFoundException()
    return result


async def create_reservation(
    user_id: UUID,
    event_id: UUID,
    event_seat_id: UUID,
    session: SessionDep,
) -> ReservationORM:
    """Atomically reserve a seat for 15 minutes."""
    reservation_id = uuid4()
    now = datetime.now(timezone.utc)
    hold_until = now + timedelta(minutes=15)

    try:
        stmt = (
            update(EventSeatORM)
            .where(
                EventSeatORM.id == event_seat_id,
                EventSeatORM.event_id == event_id,
                EventSeatORM.reservation_id.is_(None),
            )
            .values(
                reservation_id=reservation_id,
                hold_expires_at=hold_until,
            )
        )
        result = await session.execute(stmt)

        if result.rowcount == 0:
            await session.rollback()
            raise ConflictException("Seat is not available")

        reservation = ReservationORM(
            id=reservation_id,
            user_id=user_id,
            event_id=event_id,
            status=ReservationStatus.PENDING,
            expires_at=hold_until,
        )
        session.add(reservation)

        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise ConflictException("Seat is already reserved")
    except SQLAlchemyError:
        await session.rollback()
        raise DatabaseException()

    await session.refresh(reservation)
    return reservation


async def confirm_reservation(
        reservation_id: UUID,
        session: SessionDep) -> ReservationORM:
    """Confirm pending reservation"""
    now = datetime.now(timezone.utc)
    reservation = await get_reservation_by_id(reservation_id, session)
    if reservation.status != ReservationStatus.PENDING:
        raise ConflictException("This reservation is already confirmed or cancelled")
    if reservation.expires_at < now or reservation.expires_at is None:
        raise ConflictException("Your reservation has expired")

    stmt = (update(ReservationORM)
            .where(ReservationORM.id == reservation_id)
            .values(status = ReservationStatus.CONFIRMED, expires_at = None))
    stmt_event_seat = (update(EventSeatORM)
                       .where(EventSeatORM.reservation_id == reservation_id)
                       .values(hold_expires_at = None))
    try:
        await session.execute(stmt)
        result = await session.execute(stmt_event_seat)
        if result.rowcount == 0:
            await session.rollback()
            raise DatabaseException()
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        raise DatabaseException()

    
    await session.refresh(reservation)
    return reservation


async def cancel_reservation(reservation_id: UUID, session: SessionDep) -> None:
    """Cancel reservation"""
    reservation = await get_reservation_by_id(reservation_id, session)
    if reservation.status != ReservationStatus.PENDING and reservation.status != ReservationStatus.CONFIRMED:
        raise ConflictException("This reservation cannot be canceled")
    stmt = (update(ReservationORM)
            .where(ReservationORM.id == reservation_id)
            .values(status = ReservationStatus.CANCELLED))
    stmt_event = (update(EventSeatORM)
                  .where(EventSeatORM.reservation_id == reservation_id)
                  .values(reservation_id = None, hold_expires_at = None))

    try:
        result_res = await session.execute(stmt)
        result = await session.execute(stmt_event)
        if result.rowcount == 0 or result_res.rowcount == 0:
            await session.rollback()
            raise DatabaseException()
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        raise DatabaseException()
    
    return None


async def get_user_reservations(user_id: UUID, session: SessionDep) -> list[ReservationORM]:
    """Get all user reservations"""
    stmt = select(ReservationORM).where(ReservationORM.user_id == user_id).order_by(ReservationORM.created_at.desc())
    result = (await session.execute(stmt)).scalars().all()
    return list(result)

