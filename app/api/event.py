from fastapi import APIRouter, Depends, Query
from typing import List
from uuid import UUID

from app.schemas.event_schema import EventCreateRequest, EventResponse, EventUpdateRequest
from app.db.session import SessionDep
from app.db.models.user import UserORM
from app.utils.dependencies import require_role
from app.db.models.enums import UserRole
from app.crud.venue import get_venue_by_id
from app.crud.event import create_event, get_events, get_event_by_id, update_event, delete_event
from app.core.exceptions.domain import PermissionDeniedException

router = APIRouter(prefix="/events", tags=["Events"])

@router.post("", status_code=201, response_model=EventResponse)
async def create_event_endpoint(event_data: EventCreateRequest, 
                                session: SessionDep, 
                                user: UserORM = Depends(require_role(UserRole.ORGANIZER, UserRole.ADMIN))) -> EventResponse:
    """Create event, role: Organizer or Admin"""
    venue = await get_venue_by_id(event_data.venue_id, session)
    if venue.owner_id != user.id and user.role != UserRole.ADMIN:
        raise PermissionDeniedException("Not your venue")

    event = await create_event(event_data, user.id, session)
    return event


@router.get("", response_model=List[EventResponse])
async def get_events_pagination(session: SessionDep, 
                                skip: int = Query(ge=0, default=0), 
                                limit: int = Query(ge=1, le=100, default=20)) -> List[EventResponse]:
    """Get events pagination, limit, skip"""
    events = await get_events(session, skip=skip, limit=limit)
    return events


@router.get("/{event_id}", response_model=EventResponse)
async def get_event_by_id_endpoint(event_id: UUID, session: SessionDep) -> EventResponse:
    """Get event by id"""
    event = await get_event_by_id(event_id, session)
    return event


@router.patch('/{event_id}', response_model=EventResponse)
async def update_event_by_id(event_id: UUID, 
                             session: SessionDep,
                             event_data: EventUpdateRequest, 
                             user: UserORM = Depends(require_role(UserRole.ORGANIZER, UserRole.ADMIN))) -> EventResponse:
    """Patch event by id, role: organizer or admin"""
    event = await get_event_by_id(event_id, session)
    if event.organizer_id != user.id and user.role != UserRole.ADMIN:
        raise PermissionDeniedException("You do not have permission to modify this event")

    if event_data.venue_id is not None:
        new_venue = await get_venue_by_id(event_data.venue_id, session)
        if new_venue.owner_id != user.id and user.role != UserRole.ADMIN:
            raise PermissionDeniedException("Not your venue")

    new_event = await update_event(event_data, event_id, session)
    return new_event


@router.delete("/{event_id}", status_code=204)
async def delete_event_by_id(event_id: UUID, 
                             session: SessionDep, 
                             user: UserORM = Depends(require_role(UserRole.ORGANIZER, UserRole.ADMIN))) -> None:
    """Delete event by id"""
    event = await get_event_by_id(event_id, session)
    if event.organizer_id != user.id and user.role != UserRole.ADMIN:
        raise PermissionDeniedException("You do not have permission to delete this event")
    await delete_event(event_id, session)
