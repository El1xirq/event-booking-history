from fastapi import APIRouter, Depends, Query
from uuid import UUID

from app.schemas.seat_schema import SeatCreateRequest, SeatResponse, SeatUpdateRequest
from app.db.models.user import UserORM
from app.utils.dependencies import require_role, check_venue_owner
from app.db.models.enums import UserRole
from app.db.session import SessionDep
from app.crud.seat import create_seat, get_seats_by_venue, get_seat_by_id, update_seat, delete_seat
from app.crud.venue import get_venue_by_id
from app.core.exceptions.domain import PermissionDeniedException, NotFoundException


router = APIRouter(prefix="/venues/{venue_id}/seats", tags=["Seats"])


@router.post("", status_code=201, response_model=SeatResponse)
async def create_seats(venue_id: UUID, 
                       seat_data: SeatCreateRequest, 
                       session: SessionDep, 
                       user: UserORM = Depends(require_role(UserRole.ORGANIZER, UserRole.ADMIN))) -> SeatResponse:
    """Create seats"""
    await check_venue_owner(venue_id, user, session)

    seat = await create_seat(seat_data, venue_id, session)
    return seat


@router.get("", response_model=list[SeatResponse])
async def get_seats(venue_id: UUID, session: SessionDep, limit: int = Query(ge=1, le=5000, default=1000)) -> list[SeatResponse]:
    """Get seats pagination limit, by venue_id"""
    await get_venue_by_id(venue_id, session)
    seats = await get_seats_by_venue(venue_id, session, limit=limit)
    return seats


@router.get("/{seat_id}", response_model=SeatResponse)
async def get_seat_id(venue_id: UUID, seat_id: UUID, session: SessionDep) -> SeatResponse:
    """Get seats by id"""
    seat = await get_seat_by_id(seat_id, session)

    if seat.venue_id != venue_id:
        raise NotFoundException("Seat not found in this venue")
    return seat


@router.patch("/{seat_id}", response_model=SeatResponse)
async def update_seat_by_id(venue_id: UUID, 
                            seat_id: UUID, 
                            session: SessionDep, 
                            seat_data: SeatUpdateRequest, 
                            user: UserORM = Depends(require_role(UserRole.ORGANIZER, UserRole.ADMIN))) -> SeatResponse:
    """Patch seat"""
    await check_venue_owner(venue_id, user, session)
    seat = await get_seat_by_id(seat_id, session)
    if seat.venue_id != venue_id:
        raise NotFoundException("Seat not found in this venue")

    seat_update = await update_seat(seat_data, seat_id, session)
    return seat_update

@router.delete("/{seat_id}", status_code=204)
async def delete_seat_by_id(venue_id: UUID, 
                            seat_id: UUID, 
                            session: SessionDep, 
                            user: UserORM = Depends(require_role(UserRole.ORGANIZER, UserRole.ADMIN))) -> None:
    """Delete seat"""
    await check_venue_owner(venue_id, user, session)
    seat = await get_seat_by_id(seat_id, session)
    if seat.venue_id != venue_id:
        raise NotFoundException("Seat not found in this venue")
    await delete_seat(seat_id, session)