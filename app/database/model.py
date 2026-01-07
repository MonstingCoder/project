from pydantic import (
    AfterValidator,
    BeforeValidator,
    EmailStr
)
from datetime import datetime, timezone
from pwdlib import PasswordHash
from sqlmodel import Field, SQLModel
from typing import Annotated, Literal
from uuid import uuid4
from zoneinfo import ZoneInfo

import re


class AbilityCrewCreate(SQLModel):
    crew_id: int = Field(
        foreign_key='crew.id',
        primary_key=True,
        ondelete='CASCADE',
    )
    ability_id: Literal[
        1, # ability: confirm-payment
        2, # ability: give-permission
        3, # ability: manage-account
        4, # ability: manage-item
    ]

class Ability_Crew(AbilityCrewCreate, table=True):
    ability_id: int = Field(
        foreign_key='ability.id',
        primary_key=True,
        ondelete='CASCADE',
    )


class ItemTransactionCreate(SQLModel):
    item_id: int = Field(
        foreign_key='item.id',
        primary_key=True,
        ondelete='CASCADE',
    )
    transaction_id: str = Field(
        foreign_key='transaction.id',
        primary_key=True,
        ondelete='CASCADE',
    )
    quantity: int = Field(
        default=1, ge=1,
    )

class Item_Transaction(ItemTransactionCreate, table=True):
    pass


class AbilityCreate(SQLModel):
    name: Literal[
        'confirm-payment',  # id: 1
        'give-permission',  # id: 2
        'manage-account',   # id: 3
        'manage-item',      # id: 4
    ]

class Ability(AbilityCreate, table=True):
    id: int | None = Field(
        default=None, primary_key=True,
    )
    name: str = Field(
        index=True, unique=True,
    )


hasher = PasswordHash.recommended()

def get_password_hash(password):
    password_hash = hasher.hash(password)

    return password_hash

class CrewCreate(SQLModel):
    name: str = Field(
        index=True,
        min_length=3,
        unique=True,
    )
    password_hash: Annotated[
        str,
        Field(min_length=8),
        AfterValidator(get_password_hash),
    ]

class Crew(CrewCreate, table=True):
    id: int | None = Field(
        default=None, primary_key=True,
    )
    password_hash: str = Field(unique=True)


class ItemCategoryCreate(SQLModel):
    name: Literal[
        'accessory',    # id: 1
        'body',         # id: 2
        'internal',     # id: 3
    ]

class Item_Category(ItemCategoryCreate, table=True):
    id: int | None = Field(
        default=None, primary_key=True,
    )
    name: str = Field(
        index=True, unique=True,
    )


class ItemCreate(SQLModel):
    name: str = Field(
        index=True,
        unique=True,
        min_length=1,
    )
    category_id: Annotated[Literal[
        1, # category: accessory
        2, # category: body
        3, # category: internal
    ], BeforeValidator(int)]
    description: str | None = Field(
        default=None, max_length=400
    )
    price: int = Field(ge=0)
    quantity: int = Field(
        default=0, ge=0,
    )

class ItemUpdate(ItemCreate):
    name: Annotated[str | None, Field(min_length=1)] = None
    category_id: Annotated[int | None, Field(ge=1, le=3)] = None
    description: Annotated[str | None, Field(min_length=1)] = None
    price: Annotated[int | None, Field(gt=0)] = None
    quantity: Annotated[int | None, Field(ge=0)] = None

class Item(ItemCreate, table=True):
    id: int | None = Field(
        default=None, primary_key=True,
    )
    category_id: int = Field(
        foreign_key='item_category.id', ondelete='CASCADE', # ge=1, le=3,
    )


class ItemImagePathCreate(SQLModel):
    path: str
    item_id: int = Field(
        foreign_key='item.id', ondelete='CASCADE',
    )

class Item_Image_Path(ItemImagePathCreate, table=True):
    id: int | None = Field(
        default=None, primary_key=True,
    )


def phone_number_validator(phone_number):
    if not isinstance(phone_number, str):
        raise TypeError('value must be string')

    # cleaning :
    phone_number = re.sub(r"[^\d+]", "", phone_number)

    # convert to +62 :
    if phone_number.startswith("08"):
        phone_number = "+62" + phone_number[1:]
    elif phone_number.startswith("62"):
        phone_number = "+" + phone_number
    elif not phone_number.startswith("+62"):
        raise ValueError('invalid format')

    return phone_number

def get_time_now():
    now_utc = datetime.now(timezone.utc)
    now_wib = now_utc.astimezone(ZoneInfo('Asia/Jakarta'))

    return now_wib

class TrasactionCreate(SQLModel):
    name: str = Field(index=True)
    email: EmailStr
    phone_number: Annotated[
        str,
        BeforeValidator(phone_number_validator),
        Field(
            min_length=11, max_length=15,
        ),
    ]

class Transaction(TrasactionCreate, table=True):
    id: str | None = Field(
        default_factory=uuid4, primary_key=True
    )
    email: str = Field(
        index=True, unique=True,
    )
    phone_number: str
    verified: bool | None = None
    created_at: str = Field(default_factory=get_time_now)
    updated_at: str | None = None
