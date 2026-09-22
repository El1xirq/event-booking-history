from fastapi import APIRouter, Depends, Response, Request

from app.utils.dependencies import get_current_user
from app.schemas.auth_schema import UserResponse, RegistrationRequest, RegistrationData, TokenResponse, LoginRequest
from app.db.session import SessionDep
from app.utils.security import (get_password_hash, 
                                create_access_token, 
                                create_refresh_token, 
                                hash_refresh_token, 
                                verify_password,
                                verify_token)
from app.crud.auth import create_user, get_user_by_email, get_user_by_id
from app.core.config import settings
from app.crud.refresh_token import save_refresh_token, get_refresh_by_hash, revoke_all_user_tokens, revoke_refresh_token
from app.core.exceptions.domain import InvalidTokenException, PermissionDeniedException, InvalidCredentialsException


router = APIRouter(prefix="/auth", tags=['Аuthentication'])

@router.get("/me", response_model=UserResponse)
async def get_me(user = Depends(get_current_user)) -> UserResponse:
    """Get info for logged user"""
    return user


@router.post("/register", response_model=TokenResponse, status_code=201)
async def registration_user(user_data: RegistrationRequest, session: SessionDep, response: Response) -> TokenResponse:
    """Registration user, email, password"""
    password_hash = get_password_hash(user_data.password)
    user = RegistrationData(**user_data.model_dump(exclude={"password"}), hashed_password=password_hash)

    result = await create_user(user, session)
    access_token = create_access_token(user_id=result.id, role=result.role, email=result.email)
    refresh_token, expires_at = create_refresh_token(user_id=result.id)

    await save_refresh_token(user_id=result.id, 
                             token_hash=hash_refresh_token(refresh_token), 
                             expires_at=expires_at, 
                             session=session)

    response.set_cookie(key='refresh_token', value=refresh_token,
                        secure=not settings.debug,
                        httponly=True,
                        samesite="strict",
                        max_age=settings.refresh_token_expire * 24 * 3600,
                        path="/")

    return TokenResponse(access_token=access_token)


@router.post("/login", response_model=TokenResponse)
async def login_user(user_data: LoginRequest, session: SessionDep, response: Response) -> TokenResponse:
    """Login user with email and password"""

    user = await get_user_by_email(user_data.email, session)
    if user is None:
        raise InvalidCredentialsException()

    if not user.is_active:
        raise PermissionDeniedException("Account is inactive")

    if not verify_password(user_data.password, user.password_hash):
        raise InvalidCredentialsException()

    access_token = create_access_token(user_id=user.id, role=user.role, email=user.email)
    refresh_token, expires_at = create_refresh_token(user_id=user.id)
    
    await save_refresh_token(user_id=user.id, 
                             token_hash=hash_refresh_token(refresh_token), 
                             expires_at=expires_at, 
                             session=session)
    
    response.set_cookie(key='refresh_token', value=refresh_token,
                        secure=not settings.debug,
                        httponly=True,
                        samesite="strict",
                        max_age=settings.refresh_token_expire * 24 * 3600,
                        path="/")
    
    return TokenResponse(access_token=access_token)


@router.post("/refresh", response_model=TokenResponse)
async def get_refresh_user(request: Request, response: Response, session: SessionDep) -> TokenResponse:
    """Refresh token rotation, new access token"""
    refresh_token = request.cookies.get('refresh_token')

    if refresh_token is None:
        raise InvalidTokenException()

    verify_token(refresh_token, 'refresh')
    token_hash = hash_refresh_token(refresh_token)

    record = await get_refresh_by_hash(token_hash, session)
    if record is None:
        raise InvalidTokenException()
    if record.revoked_at is not None:
        await revoke_all_user_tokens(record.user_id, session)
        raise InvalidTokenException()
    await revoke_refresh_token(record, session)

    user = await get_user_by_id(record.user_id, session)

    new_access_token = create_access_token(user.id, user.role, user.email)
    new_refresh_token, expires_at = create_refresh_token(user.id)

    await save_refresh_token(user_id=user.id,
                             token_hash=hash_refresh_token(new_refresh_token), 
                             expires_at=expires_at, 
                             session=session)

    response.set_cookie(key='refresh_token', value=new_refresh_token,
                        secure=not settings.debug,
                        httponly=True,
                        samesite="strict",
                        max_age=settings.refresh_token_expire * 24 * 3600,
                        path="/")

    return TokenResponse(access_token=new_access_token)


@router.post("/logout", status_code=204)
async def logout_user(request: Request, response: Response, session: SessionDep) -> None:
    """Logout user: revoke user and clear cookie"""
    refresh_token = request.cookies.get("refresh_token")

    if refresh_token is not None:
        token_hash = hash_refresh_token(refresh_token)
        record = await get_refresh_by_hash(token_hash, session)
        if record is not None and record.revoked_at is None:
            await revoke_refresh_token(record, session)

    response.delete_cookie("refresh_token", path="/")

    








