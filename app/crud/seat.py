from uuid import UUID
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import select, update, delete

from app.db.session import SessionDep
from app.schemas.seat_schema import SeatCreateRequest, SeatUpdateRequest
from app.db.models.seat import SeatORM
from app.core.exceptions.domain import ConflictException, DatabaseException, NotFoundException

async def create_seat(seat_data: SeatCreateRequest, venue_id: UUID, session: SessionDep) -> SeatORM: 
    """Create seat"""
    seat = SeatORM(venue_id=venue_id,
                   row_number=seat_data.row_number, 
                   seat_number=seat_data.seat_number, 
                   seat_type=seat_data.seat_type)
    try: 
        session.add(seat)
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise ConflictException("Seat already exists")
    except SQLAlchemyError:
        await session.rollback()
        raise DatabaseException()
    await session.refresh(seat)
    return seat


async def get_seat_by_id(seat_id: UUID, session: SessionDep) -> SeatORM:
    """Get seat by id"""
    stmt = select(SeatORM).where(SeatORM.id == seat_id)
    seat = (await session.execute(stmt)).scalar_one_or_none()
    if seat is None: 
        raise NotFoundException()
    return seat


async def get_seats_by_venue(venue_id: UUID, session: SessionDep, limit: int) -> list[SeatORM]:
    """Getting seats in the venue"""
    stmt = select(SeatORM).where(SeatORM.venue_id == venue_id).limit(limit)
    seats = (await session.execute(stmt)).scalars().all()
    return list(seats)


async def update_seat(seat_data: SeatUpdateRequest, seat_id: UUID, session: SessionDep) -> SeatORM:
    """Patch seat by seat_id"""
    seat = await get_seat_by_id(seat_id, session)

    update_options = seat_data.model_dump(exclude_none=True)
    if not update_options:
        return seat

    stmt = update(SeatORM).where(SeatORM.id == seat_id).values(**update_options)
    try:
        await session.execute(stmt)
        await session.commit()
    except IntegrityError: 
        await session.rollback()
        raise ConflictException("The combination of row and number already exists")
    except SQLAlchemyError:
        await session.rollback()
        raise DatabaseException()

    await session.refresh(seat)
    return seat


async def delete_seat(seat_id: UUID, session: SessionDep) -> bool:
    """Delete seat by seat_id"""
    stmt = delete(SeatORM).where(SeatORM.id == seat_id).returning(SeatORM.id)

    try:
        result = (await session.execute(stmt)).scalar_one_or_none()
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise ConflictException("Cannot delete seat with reservations")
    except SQLAlchemyError:
        await session.rollback()
        raise DatabaseException()

    if result is None:
        raise NotFoundException()
    return True