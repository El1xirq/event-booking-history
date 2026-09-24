from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from uuid import UUID

from app.utils.security import verify_token
from app.crud.auth import get_user_by_id
from app.db.session import SessionDep
from app.core.exceptions.domain import InvalidTokenException
from app.db.models.enums import UserRole
from app.db.models.user import UserORM
from app.core.exceptions.domain import PermissionDeniedException

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

