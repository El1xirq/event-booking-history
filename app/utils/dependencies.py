from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from uuid import UUID

from app.utils.security import verify_token
from app.crud.auth import get_user_by_id
from app.db.session import SessionDep
from app.core.exceptions.domain import InvalidTokenException
from app.db.models.enums import UserRole
from app.db.models.user import UserORM
from app.core.exceptions.domain import PermissionDeniedException, NotFoundException
from app.crud.venue import get_venue_by_id
from app.db.models.reservation import ReservationORM
from app.crud.reservation import get_reservation_by_id


bearer_scheme = HTTPBearer()

async def get_current_user(session: SessionDep, creds: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> UserORM:
    """Extract user from Bearer token"""
    payload = verify_token(creds.credentials, "access")

    sub = payload.get("sub")
    if not sub:
        raise InvalidTokenException(detail="Invalid token payload")
    try:
        user_id = UUID(sub)
    except (TypeError, ValueError):
        raise InvalidTokenException(detail="Invalid token payload")
    
    user = await get_user_by_id(user_id, session)
    return user


def require_role(*roles: UserRole) -> UserORM:
    """Dependency factory: allow access only to specified roles"""
    async def checker(user: UserORM = Depends(get_current_user)):
        if user.role not in roles:
            raise PermissionDeniedException(detail="Insufficient permissions")
        return user
    return checker


async def check_venue_owner(
    venue_id: UUID,
    user: UserORM,
    session: SessionDep,
) -> None:
    """Raise if user is not venue owner or admin."""
    venue = await get_venue_by_id(venue_id, session)
    if venue.owner_id != user.id and user.role != UserRole.ADMIN:
        raise PermissionDeniedException("Not your venue")


async def get_owned_reservation(
    reservation_id: UUID,
    user: UserORM,
    session: SessionDep,
) -> ReservationORM:
    """Get reservation if user is owner or admin, else 404."""
    reservation = await get_reservation_by_id(reservation_id, session)
    if reservation.user_id != user.id and user.role != UserRole.ADMIN:
        raise NotFoundException("Reservation not found")
    return reservation