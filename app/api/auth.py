from fastapi import APIRouter
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/v1/auth", tags=['Аuthentication'])

