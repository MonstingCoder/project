from fastapi import APIRouter
from sqlalchemy import select
from ..database.conn import SessionDep
from ..database.model import (
    TrasactionCreate, Transaction,
)


router = APIRouter(
    prefix='/transaction', tags=['transactiion'],
)

@router.post('/')
async def test(
    *,
    q: str | None = None,
    session: SessionDep,
):
    statement = select(Transaction)
    transaction = await session.scalar(statement)

    return {
        'result': transaction,
    }