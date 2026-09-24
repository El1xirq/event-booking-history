from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from uuid import UUID
from sqlalchemy import select, update, delete
from typing import List

from app.db.session import SessionDep
from app.schemas.venue_schema import VenueCreateRequest, VenueUpdateRequest
from app.db.models.venue import VenueORM
from app.core.exceptions.domain import DatabaseException, NotFoundException, ConflictException

async def create_venue(venue_data: VenueCreateRequest, owner_id: UUID, session: SessionDep) -> VenueORM:
    """Create venue with name and address"""
    venue = VenueORM(name=venue_data.name, 
                     address=venue_data.address, 
                     description=venue_data.description, 
                     owner_id=owner_id)
    try:
        session.add(venue)
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        raise DatabaseException()

    await session.refresh(venue)
    return venue


async def get_venue_by_id(venue_id: UUID, session: SessionDep) -> VenueORM:
    """Get venue by id"""
    stmt = select(VenueORM).where(VenueORM.id==venue_id)
    venue = (await session.execute(stmt)).scalar_one_or_none()
    if venue is None:
        raise NotFoundException()
    return venue


async def get_venues(skip: int, limit: int, session: SessionDep) -> List[VenueORM]:
    """Get venues pagination"""
    stmt = select(VenueORM).offset(skip).limit(limit)
    result = (await session.execute(stmt)).scalars().all()
    return list(result)


async def update_venue(venue_data: VenueUpdateRequest, venue_id: UUID, session: SessionDep) -> VenueORM:
    """Patch venue, name, address"""
    venue = await get_venue_by_id(venue_id, session)

    update_options = venue_data.model_dump(exclude_none=True)
    if not update_options:
        return venue

    stmt = update(VenueORM).where(VenueORM.id==venue_id).values(**update_options)
    try:
        await session.execute(stmt)
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        raise DatabaseException()

    await session.refresh(venue)
    return venue


async def delete_venue(venue_id: UUID, session: SessionDep) -> bool:
    """Hard delete venue"""
    stmt = (
        delete(VenueORM)
        .where(VenueORM.id == venue_id)
        .returning(VenueORM.id)
    )
    try:
        result = await session.execute(stmt)
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise ConflictException("Cannot delete venue with existing events")
    except SQLAlchemyError:
        await session.rollback()
        raise DatabaseException()

    if result.scalar_one_or_none() is None:
        raise NotFoundException("Venue not found")
    return True