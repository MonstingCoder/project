from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from typing import Annotated
from ..database.models import Base

engine = create_async_engine('sqlite+aiosqlite:///app/database/database.db')
session = async_sessionmaker(engine, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session():
    async with session() as session_:
        yield session_

SessionDep = Annotated[AsyncSession, Depends(get_session)]
