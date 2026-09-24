from uuid import UUID
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import select, update, delete
from typing import List

from app.db.session import SessionDep
from app.db.models.event import EventORM
from app.schemas.event_schema import EventCreateRequest, EventUpdateRequest
from app.core.exceptions.domain import ConflictException, DatabaseException, NotFoundException
from app.crud.venue import get_venue_by_id

async def create_event(event_data: EventCreateRequest, organizer_id: UUID, session: SessionDep) -> EventORM:
    """Create event, event_data, organizer_id"""
    event = EventORM(**event_data.model_dump(), organizer_id=organizer_id)

    try:
        session.add(event)
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        raise DatabaseException()

    await session.refresh(event)
    return event


async def get_event_by_id(event_id: UUID, session: SessionDep) -> EventORM:
    """Get event by id"""
    stmt = select(EventORM).where(EventORM.id == event_id)
    result = (await session.execute(stmt)).scalar_one_or_none()
    if result is None:
        raise NotFoundException()
    return result


async def get_events(session: SessionDep, skip: int, limit: int) -> List[EventORM]:
    """Get events pagination, skip and limit"""
    stmt = select(EventORM).offset(skip).limit(limit)
    result = (await session.execute(stmt)).scalars().all()
    return list(result)


async def update_event(event_data: EventUpdateRequest, event_id: UUID, session: SessionDep) -> EventORM:
    """Patch event"""
    event = await get_event_by_id(event_id, session)

    update_options = event_data.model_dump(exclude_none=True)
    if not update_options:
        return event

    stmt = update(EventORM).where(EventORM.id == event_id).values(**update_options)
    try:
        await session.execute(stmt)
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        raise DatabaseException()

    await session.refresh(event)
    return event


async def delete_event(event_id: UUID, session: SessionDep) -> bool:
    """Delete event"""
    stmt = delete(EventORM).where(EventORM.id == event_id).returning(EventORM.id)
    try:
        result = (await session.execute(stmt)).scalar_one_or_none()
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise ConflictException("Cannot delete event with reservations")
    except SQLAlchemyError:
        await session.rollback()
        raise DatabaseException()

    if result is None:
        raise NotFoundException("Event not found")
    return True