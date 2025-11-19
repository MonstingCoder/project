from datetime import datetime, timezone
from pwdlib import PasswordHash
from pydantic import (
    AwareDatetime,
    AfterValidator,
    BaseModel,
    BeforeValidator,
    computed_field,
    EmailStr,
    Field,
)
from sqlalchemy import Column
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.sqlite import INTEGER, TEXT
from typing import Annotated, Literal
import re


argon2 = PasswordHash.recommended()
Base = declarative_base()

def get_time_now():
    return datetime.now(timezone.utc)

def password_hash_aval(v):
    if v is None:
        return None
    
    if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*\W).+$', v):
        raise ValueError('passwords must contain a combination of uppercase letters, lowercase letters, symbols, and numbers')
    
    return argon2.hash(v)

def phone_number_bval(v):
    if v is None:
        return None
    
    if not re.match(r'^08\d+$', v):
        raise ValueError('phone number must start with the number 08')
    
    return v
    

class User(Base):
    __tablename__ = 'user'

    id = Column(INTEGER, primary_key=True)
    role = Column(TEXT, nullable=False)
    username = Column(TEXT, index=True, nullable=False)
    password_hash = Column(TEXT, nullable=False)
    phone_number = Column(TEXT, nullable=False, unique=True)
    email = Column(TEXT, nullable=False, unique=True)
    created_at = Column(TEXT, nullable=False)
    updated_at = Column(TEXT)

class UserPublic(BaseModel):
    role: str
    username: str
    email: str
    phone_number: str
    created_at: AwareDatetime
    updated_at: AwareDatetime | None

class UserCreate(BaseModel):
    role: Literal['user'] = 'user'
    username: Annotated[str, Field(max_length=25)]
    password_hash: Annotated[
        str,
        Field(alias='password', min_length=8),
        AfterValidator(password_hash_aval),
    ]
    email: EmailStr
    phone_number: Annotated[
        str,
        Field(max_length=13, min_length=10),
        BeforeValidator(phone_number_bval),
    ]
    @computed_field
    def created_at(cls) -> AwareDatetime:
        return get_time_now()
    
class UserUpdate(BaseModel):
    username: Annotated[str | None, Field(max_length=25)] = None
    password_hash: Annotated[
        str | None,
        Field(alias='password', min_length=8),
        AfterValidator(password_hash_aval),
    ] = None
    email: EmailStr | None = None
    phone_number: Annotated[
        str | None,
        Field(max_length=13, min_length=10),
        BeforeValidator(phone_number_bval),
    ] = None
    @computed_field
    def updated_at(cls) -> AwareDatetime:
        return get_time_now()
    