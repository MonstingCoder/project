from fastapi import Depends
from pwdlib import PasswordHash
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel import (
    exists,
    select,
    text,
)
from typing import Annotated
from .models import (
    Ability,
    Item_Category,
    Crew,
    SQLModel,
)

async_engine = create_async_engine('sqlite+aiosqlite:///app/database/data.db')
async_session = async_sessionmaker(
    async_engine, expire_on_commit=False,
)

async def get_session():
    async with async_session() as session:
        yield session

SessionDep = Annotated[AsyncSession, Depends(get_session)]

async def init_db():
    async with async_engine.begin() as connection:
        await connection.execute(text('pragma foreign_keys=on'))
        await connection.run_sync(SQLModel.metadata.create_all)

    async for session in get_session():
        # check ability exists :
        if not await session.scalar(select(exists(Ability))):
            session.add_all([
                Ability(name='confirm payment'),
                Ability(name='give permission'),
                Ability(name='manage account'),
                Ability(name='manage item'),
            ])
            
            await session.commit()

        # check item category exists :
        if not await session.scalar(select(exists(Item_Category))):
            session.add_all([
                Item_Category(name='accessory'),
                Item_Category(name='body'),
                Item_Category(name='internal'),
            ])
            
            await session.commit()

        # check crew with id 0 exists :
        if not await session.scalar(select(
            exists(Crew).where(Crew.id == 0)
        )):
            hasher = PasswordHash.recommended()

            session.add(Crew(
                id=0,
                name='admin',
                password_hash=hasher.hash('admin123'),
                abilities=(
                    await session.scalars(select(Ability))
                ).all(),
            ))

            await session.commit()
