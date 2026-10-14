from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Annotated
from fastapi import Depends

from app.core.config import settings


engine = create_async_engine(settings.db_url)
session_local = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    async with session_local() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_db)]


sync_engine = create_engine(settings.db_sync_url)
sync_session = sessionmaker(sync_engine, expire_on_commit=False)
