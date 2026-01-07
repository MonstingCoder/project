from authlib.jose import jwt
from collections import defaultdict
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
from sqlmodel import select
from typing import Annotated, Literal
from ..database.conn import SessionDep
from ..database.model import (
    Ability,
    Ability_Crew,
    Crew,
)


load_dotenv(r'app/secret/.env')

router = APIRouter(prefix='/token', tags=['token'])
jwt_config = {
    'key': getenv('JWT_KEY'),
    'algorithm': 'HS256',
    'expire_minute': 10,
}


FormData = Annotated[OAuth2PasswordRequestForm, Depends()]
hasher = PasswordHash.recommended()

@router.post('/crew')
async def get_crew_token(
    form_data: FormData, session: SessionDep,
):
    try:
        # get crew :
        crew = (await session.scalar(
            select(Crew).where(Crew.name == form_data.username)
        ))
        
        # authenticate crew :
        if not crew:
            detail = f'user {form_data.username} not found'
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, detail,
            )
        
        if not hasher.verify(
            form_data.password, crew.password_hash,
        ):
            detail = 'wrong password'
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED, detail,
            )
        
        # get crew's abilities :
        abilities = (await session.execute(
            select(Ability.name)
            .select_from(Ability_Crew)
            .where(Ability_Crew.crew_id == crew.id)
            .join(Ability, Ability_Crew.ability_id == Ability.id)
        )).mappings().all()

        # make jws :
        header = {'alg': jwt_config['algorithm']}
        payload = {
            'sub': crew.id,
            'exp': datetime.now(timezone.utc) + timedelta(minutes=jwt_config['expire_minute']),
            'abilities': [i['name'] for i in abilities],
        }
        token = jwt.encode(
            header,
            payload,
            jwt_config['key'],
        )
        jws = {
            'type': 'bearer',
            'token': token
        }

        return jws
    
    except HTTPException:
        raise

    except Exception as e:
        detail = {
            'status': type(e).__name__,
            'message': str(e),
        }
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, detail,
        )


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
