from fastapi import APIRouter, Depends, Query
from typing import List
from uuid import UUID

from app.utils.dependencies import require_role
from app.db.models.user import UserORM
from app.db.models.enums import UserRole
from app.db.session import SessionDep
from app.schemas.venue_schema import VenueCreateRequest, VenueResponse, VenueUpdateRequest
from app.crud.venue import create_venue, get_venues, get_venue_by_id, update_venue, delete_venue
from app.core.exceptions.domain import PermissionDeniedException

router = APIRouter(prefix="/venues", tags=["Venue"])


@router.post("", status_code=201, response_model=VenueResponse)
async def create_venue_endpoint(session: SessionDep, 
                       venue_data: VenueCreateRequest, 
                       user: UserORM = Depends(require_role(UserRole.ORGANIZER, UserRole.ADMIN))) -> VenueResponse:
    """Create venue, role: organizer or admin, data: name, address, description"""
    venue = await create_venue(venue_data=venue_data, owner_id=user.id, session=session)
    return venue


@router.get("", response_model=List[VenueResponse])
async def get_venues_pagination(session: SessionDep,
                                skip: int = Query(ge=0, default=0), 
                                limit: int = Query(ge=1, le=100, default=20)) -> List[VenueResponse]:
    """Get list venues, pagination: offset, limit"""
    venues = await get_venues(skip=skip, limit=limit, session=session)
    return venues


@router.get("/{venue_id}", response_model=VenueResponse)
async def get_venue_by_id_endpoint(venue_id: UUID, session: SessionDep) -> VenueResponse:
    """Get venue by id"""
    venue = await get_venue_by_id(venue_id=venue_id, session=session)
    return venue


@router.patch("/{venue_id}", response_model=VenueResponse)
async def update_venue_by_id(venue_id: UUID, 
                             venue_data: VenueUpdateRequest, 
                             session: SessionDep, 
                             user: UserORM = Depends(require_role(UserRole.ORGANIZER, UserRole.ADMIN))) -> VenueResponse:
    """Update venue, role: organizer, admin"""
    venue = await get_venue_by_id(venue_id=venue_id, session=session)
    if venue.owner_id != user.id and user.role != UserRole.ADMIN:
        raise PermissionDeniedException(detail="You do not have permission to modify this room")

    return await update_venue(venue_data, venue_id, session)


@router.delete("/{venue_id}", status_code=204)
async def delete_venue_by_id(venue_id: UUID, 
                             session: SessionDep,
                             user: UserORM = Depends(require_role(UserRole.ORGANIZER, UserRole.ADMIN))) -> None:
    """Delete venue by id"""
    venue = await get_venue_by_id(venue_id, session)
    if user.id != venue.owner_id and user.role != UserRole.ADMIN:
        raise PermissionDeniedException(detail="You do not have permission to delete this room")
    await delete_venue(venue_id, session)
