from fastapi import (
    APIRouter,
    HTTPException,
    UploadFile,
    status,
    Query,
)
from pathlib import Path
from shutil import copyfileobj
from sqlmodel import func, select
from typing import Annotated
from uuid import uuid4
from .token import CurrentCrew
from ..database.conn import SessionDep
from ..database.model import (
    ItemCreate, ItemUpdate, Item,
    ItemImagePathCreate, Item_Image_Path,
    Item_Category,
)

router = APIRouter(
    prefix='/item', tags=['item'],
)


@router.get('/')
async def read_items(
    *,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    session: SessionDep,
):
    statement = (
        select(Item)
        .offset(offset)
        .limit(limit)
        .subquery()
    )
    statement = (
        select(
            statement.c.id.label('item_id'),
            statement.c.name,
            statement.c.price,
            statement.c.quantity,
            statement.c.description,
            Item_Category.id.label('category_id'),
            Item_Category.name.label('category'),
            func.group_concat(Item_Image_Path.id, ',').label('image_id'),
            func.group_concat(Item_Image_Path.path, ',').label('path'),
        )
        .select_from(statement)
        .outerjoin(Item_Category, statement.c.category_id == Item_Category.id)
        .outerjoin(Item_Image_Path, statement.c.id == Item_Image_Path.item_id)
        .group_by(statement.c.id)
    )
    result = await session.execute(statement)
    result = result.mappings().all()

    if not result:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    
    data = []
    for row in result:
        row = dict(row)

        if row['image_id']:
            row['image_id'] = [int(i) for i in row['image_id'].split(',')]

        if row['path']:
            row['path'] = row['path'].split(',')

        data.append(row)

    return data


@router.get('/{item_id}')
async def read_item(
    *,
    item_id: int,
    session: SessionDep,
):
    statement = (
        select(
            Item.id.label('item_id'),
            Item.name,
            Item.price,
            Item.quantity,
            Item.description,
            Item_Category.id.label('category_id'),
            Item_Category.name.label('category'),
            func.group_concat(Item_Image_Path.id, ',').label('image_id'),
            func.group_concat(Item_Image_Path.path, ',').label('path'),
        )
        .select_from(Item)
        .outerjoin(Item_Category, Item.category_id == Item_Category.id)
        .outerjoin(Item_Image_Path, Item.id == Item_Image_Path.item_id)
        .group_by(Item.id)
        .where(Item.id == item_id)
    )
    item = await session.execute(statement)
    item = item.mappings().first()

    if not item:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail='item not found',
        )
    
    item = dict(item)

    if item['image_id']:
        item['image_id'] = [int(i) for i in item['image_id'].split(',')]
    
    if item['path']:
        item['path'] = item['path'].split(',')

    return item


@router.post('/')
async def create_item(
    *,
    current_crew: CurrentCrew,
    data: ItemCreate,
    session: SessionDep,
):
    try :
        if 'manage-item' not in current_crew['abilities']:
            raise HTTPException(status.HTTP_403_FORBIDDEN)
        
        item = ItemCreate(
            name=data.name,
            category_id=data.category_id,
            description=data.description,
            price=data.price,
            quantity=data.quantity,
        )
        item = Item.model_validate(item)

        session.add(item)
        await session.commit()
        
        return {
            'action': 'create item',
            'status': 'success',
            'item_id': item.id,
        }
    
    except HTTPException:
        raise
    
    except Exception as e:
        detail = {
            'type': type(e).__name__,
            'message': str(e),
        }
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail)


@router.put('/{item_id}')
async def update_item(
    *,
    item_id: int,
    data: ItemUpdate,
    current_crew: CurrentCrew,
    session: SessionDep,
):
    if 'manage-item' not in current_crew['abilities']:
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    
    item = await session.get(Item, item_id)
    if not item:
        detail = 'item not found'
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail)
    
    data = data.model_dump(exclude_unset=True)
    item = item.sqlmodel_update(data)

    session.add(item)
    await session.commit()
    await session.refresh(item)

    return {
        'action': 'update item',
        'status': 'success',
        'result': item,
    }


@router.delete('/{item_id}')
async def delete_item(
    *,
    item_id: int,
    current_crew:CurrentCrew,
    session: SessionDep,
):
    if 'manage-item' not in current_crew['abilities']:
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    
    item = await session.get(Item, item_id)
    if not item:
        detail = 'item not found'
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail)
    
    await session.delete(item)
    await session.commit()

    return {
        'action': f'delete item: {item.name}',
        'status': 'success',
    }


ALLOWED_IMAGE_TYPE = [
    'image/jpg',
    'image/jpeg',
    'image/webp',
]
IMAGE_MAX_SIZE = 2 * 1024 ** 2
IMAGE_DIR = Path('app/static/images')

@router.post('/image/{item_id}')
async def add_images(
    *,
    current_crew: CurrentCrew,
    item_id: int,
    images: list[UploadFile],
    session: SessionDep,
):
    if 'manage-item' not in current_crew['abilities']:
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    
    item = await session.get(Item, item_id)
    if not item:
        detail = 'item not found'
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail)
    
    for image in images:
        # vailidate images :
        if image.size > IMAGE_MAX_SIZE:
            detail = f'max image size: {IMAGE_MAX_SIZE / 1024 ** 2} mb'
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail)

        if image.content_type not in ALLOWED_IMAGE_TYPE:
            detail = f'allowed image type: {', '.join(ALLOWED_IMAGE_TYPE)}'
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail)
    
        # save images :
        image_name = fr'{uuid4()}.webp'
        image_path = IMAGE_DIR / image_name
        
        with image_path.open('wb') as buffer:
            copyfileobj(image.file, buffer)
        
        # save in database :
        image_path = ItemImagePathCreate(
            path=fr'static/images/{image_name}', item_id=item.id,
        )
        image_path = Item_Image_Path.model_validate(image_path)

        session.add(image_path)
    
    await session.commit()
    
    return {
        'action': 'add images',
        'status': 'success',
    }


@router.delete('/image/{image_id}')
async def delete_image(
    *,
    image_id: int,
    current_crew: CurrentCrew,
    session: SessionDep,
):
    if 'manage-item' not in current_crew['abilities']:
            raise HTTPException(status.HTTP_403_FORBIDDEN)
    
    image = await session.get(Item_Image_Path, {'id': image_id})
    if not image:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    
    await session.delete(image)
    await session.commit()

    return {
        'action': f'delete {image.path}',
        'status': 'success',
    }
