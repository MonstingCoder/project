from fastapi import (
    APIRouter,
    HTTPException,
    status,
)

router = APIRouter(prefix='/token', tags=['token'])


@router.get("/login")
def login():
    detail = {'message': 'unfinished'}

    raise HTTPException(status.HTTP_418_IM_A_TEAPOT, detail)
