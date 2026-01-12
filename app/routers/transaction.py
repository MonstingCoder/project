from dotenv import load_dotenv
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    HTTPException,
    Query,
    Request,
    status,
)
from os import getenv
from pathlib import Path
from pydantic import  BaseModel, Field
from sqlmodel import func, select
from typing import Annotated
from uuid import UUID
from .token import CurrentCrew
from ..database.conn import SessionDep
from ..database.model import (
    Item,
    ItemTransactionCreate, Item_Transaction,
    TrasactionCreate, Transaction, get_time_now,
)
from ..email import send_payment_email
import json


router = APIRouter(
    prefix='/transaction', tags=['transactiion'],
)
IMAGE_DIR = Path('app/static/images')


load_dotenv(r'app/secret/.env')


class ItemDetail(BaseModel):
    item_id: Annotated[int, Field(ge=0)]
    quantity: Annotated[int, Field(ge=1)]


class TransactionModel(TrasactionCreate):
    item_detail: list[ItemDetail]


@router.get('/')
async def read_transactions(
    *,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1)] = 20,

    current_crew: CurrentCrew,
    session: SessionDep,
):
    if 'confirm-payment' not in current_crew['abilities']:
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    
    items = (
        select(
            Item_Transaction.transaction_id,
            func.json_group_array(
                func.json_object(
                    'name', Item.name,
                    'quantity', Item_Transaction.quantity,
                    'price', Item.price,
                )
            ).label('items')
        )
        .select_from(Item_Transaction)
        .outerjoin(Item, Item_Transaction.item_id == Item.id)
        .offset(offset)
        .limit(limit)
        .group_by(Item_Transaction.transaction_id)
        .subquery()
    )
    transactions = (
        select(Transaction, items.c['items'])
        .select_from(items)
        .outerjoin(Transaction, items.c['transaction_id'] == Transaction.id)
    )
    transactions = await session.execute(transactions)
    transactions = transactions.mappings().all()

    for i in range(len(transactions)):
        transactions[i] = dict(transactions[i])
        transactions[i]['items'] = json.loads(transactions[i]['items'])
        
        transactions[i]['total'] = 0
        for transaction_item in transactions[i]['items']:
            transactions[i]['total'] += transaction_item['quantity'] * transaction_item['price']

    return transactions


@router.get('/{transaction_id}')
async def read_transaction(
    *,
    transaction_id: UUID,
    
    session: SessionDep,
):
    items = (
        select(
            Item_Transaction.transaction_id,
            func.json_group_array(
                func.json_object(
                    'name', Item.name,
                    'quantity', Item_Transaction.quantity,
                    'price', Item.price,
                )
            ).label('items')
        )
        .select_from(Item_Transaction)
        .outerjoin(Item, Item_Transaction.item_id == Item.id)
        .where(Item_Transaction.transaction_id == transaction_id)
        .group_by(Item_Transaction.transaction_id)
        .subquery()
    )
    transaction = (
        select(Transaction, items.c['items'])
        .select_from(items)
        .outerjoin(Transaction, items.c['transaction_id'] == Transaction.id)
    )
    transaction = await session.execute(transaction)
    transaction = transaction.mappings().one_or_none()

    transaction = dict(transaction)
    transaction['items'] = json.loads(transaction['items'])
    
    transaction['total'] = 0
    for transaction_item in transaction['items']:
        transaction['total'] += transaction_item['quantity'] * transaction_item['price']

    return transaction


@router.post('/')
async def create_transaction(
    *,
    data: TransactionModel,
    
    background_tasks: BackgroundTasks,
    session: SessionDep,
):
    requested_item_ids = [item.item_id for item in data.item_detail]

    async with session.begin():
        # item validation :
        statement = (
            select(Item)
            .where(Item.id.in_(requested_item_ids))
            .with_for_update()
        )
        result = await session.scalars(statement)
        items = {item.id: item for item in result.all()}
    if len(items) != len(requested_item_ids):
        detail = 'salah satu item tidak ditemukan'
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail)
    
    # stock validation :
    for item_req in data.item_detail:
        item = items[item_req.item_id]
        if item_req.quantity > item.quantity:
            detail = f'permintaan untuk {item.name} melebihi stok yang tersedia'
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail)
    
    # atomic transaction :
    async with session.begin():
        transaction = Transaction(
            name=data.name,
            email=data.email,
            phone_number=data.phone_number,
        )
        session.add(transaction)
        await session.flush()  # supaya transaction.id tersedia

        detail_transaction = {
            "items": [],
            "total": 0,
        }

        for item_req in data.item_detail:
            item = items[item_req.item_id]

            # Simpan item transaksi
            item_tx = Item_Transaction(
                item_id=item.id,
                transaction_id=transaction.id,
                quantity=item_req.quantity,
            )
            session.add(item_tx)

            # Kurangi stok
            item.quantity -= item_req.quantity

            subtotal = item.price * item_req.quantity
            detail_transaction["items"].append({
                "name": item.name,
                "price": item.price,
                "quantity": item_req.quantity,
            })
            detail_transaction["total"] += subtotal
    
    background_tasks.add_task(
        send_payment_email,
        data.email,
        detail_transaction,
        getenv("PAYMENT_PROOF_URL"),
        transaction.id,
    )

    return {"referral_code": transaction.id}


@router.patch('/')
async def change_status(
    *,
    transaction_id: Annotated[UUID, Body()],
    confirm: Annotated[bool, Body()],

    current_crew: CurrentCrew,
    session: SessionDep,
):
    if 'confirm-payment' not in current_crew['abilities']:
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    
    transaction = await session.get(Transaction, transaction_id)
    if not transaction:
        detail = 'transaction not found'
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail)
    
    transaction.confirmed = confirm
    transaction.updated_at = get_time_now()

    session.add(transaction)
    await session.commit()

    return {'success': True}
