from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.utils.security import verify_token
from app.crud.auth import get_user_by_id
from app.db.session import SessionDep
from app.core.exceptions.domain import InvalidTokenException

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(session: SessionDep, token: str = Depends(oauth2_scheme)):
    payload = verify_token(token)

    sub = payload.get("sub")
    if sub is None:
        raise InvalidTokenException(detail="Invalid token payload")
    try:
        user_id = int(sub)
    except (TypeError, ValueError):
        raise InvalidTokenException(detail="Invalid token payload")
    
    user = await get_user_by_id(user_id, session)
    return user


    