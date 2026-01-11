from collections import defaultdict
from fastapi import (
    APIRouter,
    Body,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.exc import IntegrityError
from sqlmodel import func, select
from typing import Annotated, Literal
from .token import CurrentCrew
from ..database.conn import SessionDep
from ..database.model import (
    Ability,
    Ability_Crew, AbilityCrewCreate,
    Crew, CrewCreate,
)
import json


router = APIRouter(
    prefix='/crew', tags=['crew'],
)


@router.get('/')
async def read_crews(
    *,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1)] = 20,
    
    current_crew: CurrentCrew,
    session: SessionDep,
):
    if 'manage-account' not in current_crew['abilities']:
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    
    try:
        # get crew and their ability :
        statement = (
            select(Crew)
            .offset(offset)
            .limit(limit)
            .subquery()
        )
        statement = (
            select(
                statement.c.id,
                statement.c.name,
                func.group_concat(Ability.name, ',').label('ability'),
            )
            .select_from(statement)
            .join(Ability_Crew, statement.c.id == Ability_Crew.crew_id)
            .join(Ability, Ability_Crew.ability_id == Ability.id)
            .group_by(statement.c.id)
        )
        result = await session.execute(statement)
        result = result.mappings().all()

        data = []
        for row in result:
            row = dict(row)
            row['ability'] = row["ability"].split(',')
            data.append(row)

        return data
    
    except HTTPException:
        raise
    
    except Exception as e:
        detail = {
            'type': type(e).__name__, 'message': str(e),
        }
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, detail,
        )


@router.get('/{crew_id}')
async def read_crew(
    *,
    crew_id: int,

    current_crew: CurrentCrew,
    session: SessionDep,
):
    for ability in ['manage-account', 'give-permission']:
        if ability not in current_crew['abilities']:
            raise HTTPException(status.HTTP_403_FORBIDDEN)
    
    crew = (
        select(Crew.name, func.json_group_array(Ability.name).label('abilities'))
        .select_from(Crew)
        .outerjoin(Ability_Crew, Crew.id == Ability_Crew.crew_id)
        .outerjoin(Ability, Ability_Crew.ability_id == Ability.id)
        .where(Crew.id == crew_id)
        .group_by(Crew.id)
    )
    crew = await session.execute(crew)
    crew = crew.mappings().first()
    crew = dict(crew)
    crew['abilities'] = json.loads(crew['abilities'])

    if not crew:
        detail = 'crew not found'
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail)
    
    return {'crew': crew}


ability_map = {
    'confirm-payment': 1,  # id: 1
    'manage-account': 3,   # id: 3
    'manage-item': 4,      # id: 4
}

@router.post('/')
async def create_crew(
    *,
    crew: CrewCreate,
    ability_data: list[Literal[
        "confirm-payment",
        "manage-account",
        "manage-item"
    ]],

    current_crew: CurrentCrew,
    session: SessionDep,
):
    '''
    catatan :\n
    ini adalah endpoint untuk membuat crew dengan ability nya.

    '''
    if 'manage-account' not in current_crew['abilities']:
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    
    crew = Crew.model_validate(crew)
    
    try:
        async with session.begin():
            session.add(crew)
    except IntegrityError as e:
        detail = str(e.orig)
        if 'name' in detail:
            detail = 'name already exists'
        
        if 'password_hash' in detail:
            detail = 'password already exists'
        
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail)
    
    for i, j in enumerate(ability_data):
        ability_data[i] = ability_map[j]
    
    async with session.begin():
        for ability_id in ability_data:
            ability = AbilityCrewCreate(
                crew_id=crew.id, ability_id=ability_id,
            )
            ability = Ability_Crew.model_validate(ability)

            session.add(ability)
    
    return {'success': True}
