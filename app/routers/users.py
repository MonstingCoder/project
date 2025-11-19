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

@router.get('/{id}', response_model=models.UserPublic)
@default_e_h()
async def read_user(
    *,
    id: Annotated[int, Path(ge=0)],
    session: conn.SessionDep,
):
    data = await session.get(models.User, id)
    if not data:
        print('ok')
        detail = {
            'status': status.HTTP_404_NOT_FOUND,
            'message': 'user not found',
            'value': data
        }
        
        raise ValueError(detail)
    
    return data


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
    id: Annotated[int, Path(ge=0)],
    payload: models.UserUpdate,
    session: conn.SessionDep,
):
    data = await session.get(models.User, id)
    if not data:
        print('ok')
        detail = {
            'status': status.HTTP_404_NOT_FOUND,
            'message': 'user not found',
            'value': data
        }
        
        raise ValueError(detail)
    
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(data, field, value)

    await session.commit()
    await session.refresh(data)

    return data

@router.delete('/{id}', response_model=models.UserPublic)
@default_e_h()
async def delete_user(
    *,
    id: Annotated[int, Path(ge=0)],
    session: conn.SessionDep
):
    data = await session.get(models.User, id)

    await session.delete(data)
    await session.commit()

    return data
