from uuid import UUID
from sqlalchemy import select

from app.db.models.event_seat import EventSeatORM
from app.db.session import SessionDep
from app.core.exceptions.domain import NotFoundException

async def get_event_seat_by_id(event_seat: UUID, session: SessionDep) -> EventSeatORM:
    """Get event_seat by id or raise NotFoundException"""
    stmt = select(EventSeatORM).where(EventSeatORM.id == event_seat)
    result = (await session.execute(stmt)).scalar_one_or_none()
    if result is None:
        raise NotFoundException("Event seat not found")
    return result


async def get_event_seats_by_event(event_id: UUID, session: SessionDep, limit: int) -> list[EventSeatORM]:
    """List event_seats for an event."""
    stmt = (
        select(EventSeatORM)
        .where(EventSeatORM.event_id == event_id)
        .limit(limit)
    )
    return list((await session.execute(stmt)).scalars().all())