from fastapi import Depends
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
from .model import (
    Ability, AbilityCreate,
    Ability_Crew, AbilityCrewCreate,
    Item_Category, ItemCategoryCreate,
    Crew, CrewCreate,
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

    async with async_session() as session:
        # check ability exists :
        statement = select(exists(Ability))
        ability = await session.scalar(statement)

        if not ability:
            abilities = [
                AbilityCreate(name='confirm-payment'),
                AbilityCreate(name='manage-account'),
                AbilityCreate(name='manage-item'),
            ]
            abilities = [Ability.model_validate(ability) for ability in abilities]
            
            session.add_all(abilities)

        # check item category exists :
        statement = select(exists(Item_Category))
        item_category = await session.scalar(statement)

        if not item_category:
            item_categories = [
                ItemCategoryCreate(name='accessory'),
                ItemCategoryCreate(name='body'),
                ItemCategoryCreate(name='core'),
            ]
            item_categories = [Item_Category.model_validate(item_category) for item_category in item_categories]

            session.add_all(item_categories)

        # commit abilities and categories :
        await session.commit()

        # check crew with id 0 exists :
        statement = select(
            exists(Crew).where(Crew.id == 0)
        )
        crew = await session.scalar(statement)
        if not crew:
            # create crew :
            crew = CrewCreate(
                name='admin', password_hash='admin123',
            )
            crew = Crew.model_validate(crew)
            crew.id = 0

            # commit crew :
            session.add(crew)
            await session.commit()

            # create ability crews :
            abilitiy_crews = [AbilityCrewCreate(
                crew_id=0, ability_id=i,
            ) for i in range(1, 4)]
            abilitiy_crews = [Ability_Crew.model_validate(i) for i in abilitiy_crews]

            # commit abilitiy_crews :
            session.add_all(abilitiy_crews)
            await session.commit()


async def close_db():
    await async_engine.dispose()