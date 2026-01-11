from fastapi import (
    APIRouter,
    Form,
    HTTPException,
    Query,
    status,
    UploadFile,
)
from pathlib import Path
from shutil import copyfileobj
from sqlmodel import func, select
from typing import Annotated
from uuid import UUID, uuid4
from .token import CurrentCrew
from ..database.conn import SessionDep
from ..database.model import (
    Transaction,
    PaymentProofCreate, Payment_Proof,
)
import json


router = APIRouter(
    prefix='/payment-proof', tags=['payment-proof'],
)

IMAGE_DIR = Path(r'app/static/images')


@router.get('/')
async def read_payment_proof(
    *,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1)] = 1,
    
    current_crew: CurrentCrew,
    session: SessionDep,
):
    '''
    endpoint ini digunakan untuk menampilkan daftar bukti transaksi
    
    '''
    if 'confirm-payment' not in current_crew['abilities']:
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    
    payment_proofs = (
        select(Payment_Proof.transaction_id, func.json_group_array(Payment_Proof.image_path).label('image_paths'))
        .group_by(Payment_Proof.transaction_id)
        .offset(offset)
        .limit(limit)
    )
    payment_proofs = await session.execute(payment_proofs)
    payment_proofs = payment_proofs.mappings().all()

    for i, payment_proof in enumerate(payment_proofs):
        payment_proof = dict(payment_proof)
        payment_proof['image_paths'] = json.loads(payment_proof['image_paths'])
        payment_proofs[i] = payment_proof

    return payment_proofs


@router.post('/')
async def upload_payment_proof(
    *,
    transaction_id: Annotated[UUID, Form()],
    image: UploadFile,

    session: SessionDep,
):
    '''
    endopint ini digunakan untuk mengunggah bukti transaksi dengan memasukkan kode referal
    dan gambar yang berisi bukti pembayaran, pengguna dapat meunguploadnya berkali-kali selama
    status transaksi masih null / belum dikonfirmasi.
    
    '''
    transaction = await session.get(Transaction, transaction_id)
    if not transaction:
        detail = 'transaction not found'
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail)
    
    # PERHATIKAN BAGIAN INI ! ! !
    if transaction.confirmed is not None:
        detail = 'your transaction has been confirmed,' \
        'please chechk your email.'
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail)
    
    if image.size > 2 * 1024 ** 3:
        detail = 'max image size: 3mb'
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail)
    
    image_name = fr'{uuid4()}.webp'
    image.filename = IMAGE_DIR / image_name

    with image.filename.open('wb') as buffer:
        copyfileobj(image.file, buffer)
    
    payment_proof = PaymentProofCreate(
        transaction_id=transaction_id, image_path=fr'/static/images/{image_name}'
    )
    payment_proof = Payment_Proof.model_validate(payment_proof)

    session.add(payment_proof)
    await session.commit()

    return {'success': True}
