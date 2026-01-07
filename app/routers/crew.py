from collections import defaultdict
from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    status,
)
from sqlmodel import func, select
from typing import Annotated
from ..database.conn import SessionDep
from ..database.model import (
    Ability,
    Ability_Crew,
    Crew,
)


router = APIRouter(
    prefix='/crew', tags=['crew'],
)


@router.get('/')
async def read_crews(
    session: SessionDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1)] = 20,
):
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
