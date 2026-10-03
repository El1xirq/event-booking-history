from fastapi import APIRouter, Depends
from uuid import UUID

from app.schemas.reservation_schema import ReservationResponse, ReservationCreateRequest
from app.db.models.user import UserORM
from app.utils.dependencies import require_role, get_owned_reservation
from app.db.models.enums import UserRole
from app.db.session import SessionDep
from app.crud.event_seat import get_event_seat_by_id
from app.crud.reservation import (create_reservation, 
                                  confirm_reservation, 
                                  cancel_reservation, 
                                  get_user_reservations, 
                                  get_reservation_by_id)
from app.core.exceptions.domain import NotFoundException



router = APIRouter(prefix="/reservations", tags=["Reservations"])


@router.post("", response_model=ReservationResponse, status_code=201)
async def create_reservation_api(rvn_data: ReservationCreateRequest,
                                 session: SessionDep, 
                                 user: UserORM = Depends(require_role(UserRole.CUSTOMER, UserRole.ADMIN))
                                 ) -> ReservationResponse:
    """Create seat reservation"""
    event_seat = await get_event_seat_by_id(rvn_data.event_seat_id, session)
    if event_seat.event_id != rvn_data.event_id:
        raise NotFoundException("Event seat not found")
    reservation = await create_reservation(user_id=user.id,
                                            event_id=rvn_data.event_id,
                                            event_seat_id=rvn_data.event_seat_id, 
                                            session=session)
    return reservation


@router.patch("/{reservation_id}/confirm", response_model=ReservationResponse)
async def confirm_reservation_api(reservation_id: UUID, 
                                  session: SessionDep, 
                                  user: UserORM = Depends(require_role(UserRole.CUSTOMER, UserRole.ADMIN))
                                  ) -> ReservationResponse:
    """Confirm reservation"""
    await get_owned_reservation(reservation_id, user, session)
    reservation = await confirm_reservation(reservation_id, session)
    return reservation


@router.delete("/{reservation_id}", status_code=204)
async def cancel_reservation_api(reservation_id: UUID, 
                                 session: SessionDep,
                                 user: UserORM = Depends(require_role(UserRole.CUSTOMER, UserRole.ADMIN))
                                 ) -> None:
    """Cancel reservation"""
    await get_owned_reservation(reservation_id, user, session)
    await cancel_reservation(reservation_id, session)


@router.get("", response_model=list[ReservationResponse])
async def get_reservations(session: SessionDep, 
                           user: UserORM = Depends(require_role(UserRole.CUSTOMER, UserRole.ADMIN))
                           ) -> list[ReservationResponse]:
    """Get reservations user"""
    reservations =  await get_user_reservations(user.id, session)
    return reservations


@router.get("/{reservation_id}", response_model=ReservationResponse)
async def get_reservation_by_id_api(reservation_id: UUID, 
                                session: SessionDep, 
                                user: UserORM = Depends(require_role(UserRole.CUSTOMER, UserRole.ADMIN))
                                ) -> ReservationResponse:
    """Get reservation by id"""
    reservation = await get_owned_reservation(reservation_id, user, session)
    return reservation


