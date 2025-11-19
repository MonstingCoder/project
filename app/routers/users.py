from fastapi import (
    APIRouter,
    HTTPException,
    Path,
    status,
    Query,
)
from sqlalchemy import select
from typing import Annotated
from ..database import conn, models
from ..helpers import default_e_h


router = APIRouter(prefix='/users', tags=['user'])


@router.get('/', response_model=list[models.UserPublic])
@default_e_h()
async def read_users(
    *,
    limit: Annotated[int, Query(ge=1, le=25)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
    session: conn.SessionDep,
):
    statement = select(models.User).offset(offset).limit(limit)
    data = await session.execute(statement)

    return data.scalars()


@router.post('/', response_model=models.UserPublic)
@default_e_h()
async def create_user(
    *,
    payload: models.UserCreate,
    session: conn.SessionDep,
):
    payload = models.User(**payload.model_dump())
    
    session.add(payload)
    await session.commit()
    await session.refresh(payload)

    return payload


@router.patch('/{id}', response_model=models.UserPublic)
@default_e_h()
async def update_user(
    *,
    id: Annotated[int, Path(ge=1)],
    payload: models.UserUpdate,
    session: conn.SessionDep
):
    data = await session.get(models.User, id)
    if not data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail='user not found')
    
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(data, field, value)
    session.add(data)
    await session.commit()
    await session.refresh(data)

    return data
