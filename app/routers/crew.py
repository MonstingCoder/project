from fastapi import APIRouter
from .token import CurrentCrew

router = APIRouter(prefix='/crew', tags=['crew'])

@router.post('/')
async def test(current_crew: CurrentCrew):
    return current_crew
