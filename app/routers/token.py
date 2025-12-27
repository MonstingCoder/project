from authlib.jose import jwt
from datetime import (
    datetime,
    timedelta,
    timezone,
)
from dotenv import load_dotenv
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from fastapi.security import (
    OAuth2PasswordBearer, OAuth2PasswordRequestForm,
)
from os import getenv
from pwdlib import PasswordHash
from sqlalchemy.orm import selectinload
from sqlmodel import select
from typing import Annotated, Literal
from ..database.conn import SessionDep
from ..database.models import Ability, Crew

load_dotenv(r'app/secret/.env')
router = APIRouter(prefix='/token', tags=['token'])

hasher = PasswordHash.recommended()
jwt_config = {
    'key': getenv('JWT_KEY'),
    'algorithm': 'HS256',
    'expire_minute': 20,
}

FormData = Annotated[OAuth2PasswordRequestForm, Depends()]

@router.post('/crew')
async def get_crew_token(
    form_data: FormData, session: SessionDep,
):
    # get crew :
    crew = await session.scalar(
        select(Crew)
        .options(selectinload(Crew.abilities))
        .where(Crew.name == form_data.username)
    )

    # authenticate crew:
    if not crew:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=f'user {form_data.username} not found',
        )
    if not hasher.verify(
        form_data.password, crew.password_hash,
    ):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail='wrong password',
        )
    
    # jwt :
    token = jwt.encode(
        {'alg': jwt_config['algorithm']},
        {
            'sub': crew.id,
            'abilities': [ability.name for ability in crew.abilities],
            'exp': datetime.now(timezone.utc) + timedelta(minutes=jwt_config['expire_minute']),
        },
        jwt_config['key'],
    )

    return {
        'type': 'bearer',
        'token': token,
    }

crew_oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token/crew')
CrewToken = Annotated[str, Depends(crew_oauth2_scheme)]

def get_current_user(token: CrewToken):
    try:
        claims = jwt.decode(
            token, jwt_config['key'],
        )
        claims.validate()

        return {
            'sub': claims['sub'],
            'abilities': claims['abilities'],
        }
    except Exception as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=e.args)

CurrentCrew = Annotated[
    dict[Literal['sub', 'abilities'], int | list[Ability]], Depends(get_current_user),
]
