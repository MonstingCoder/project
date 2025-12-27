from sqlmodel import (
    Field,
    SQLModel,
    Relationship,
)
from uuid import uuid4

class Ability_Crew(SQLModel, table=True):
    crew_id: int = Field(
        foreign_key='crew.id',
        primary_key=True,
        ondelete='CASCADE',
    )
    ability_id: int = Field(
        foreign_key='ability.id',
        primary_key=True,
        ondelete='CASCADE',
    )

class Item_Transaction(SQLModel, table=True):
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
    quantity: int

    items: 'Item' = Relationship(back_populates='item_transactions')
    transactions: 'Transaction' = Relationship(back_populates='item_transactions')

class Ability(SQLModel, table=True):
    id: int | None = Field(
        default=None, primary_key=True,
    )
    name: str

    crews: list['Crew'] = Relationship(
        back_populates='abilities', link_model=Ability_Crew,
    )

class Crew(SQLModel, table=True):
    id: int | None = Field(
        default=None, primary_key=True,
    )
    name: str = Field(
        index=True, unique=True,
    )
    password_hash: str

    abilities: list[Ability] = Relationship(
        back_populates='crews', link_model=Ability_Crew,
    )

class Item_Category(SQLModel, table=True):
    id: int | None = Field(
        default=None, primary_key=True,
    )
    name: str = Field(index=True)

    items: list['Item'] = Relationship(back_populates='item_category')

class Item(SQLModel, table=True):
    id: int | None = Field(
        default=None, primary_key=True,
    )
    name: str = Field(index=True)
    category: int = Field(foreign_key='item_category.id')
    description: str
    price: int

    item_category: Item_Category | None = Relationship(back_populates='items')
    item_image_paths: list['Item_Image_Path'] = Relationship(back_populates='item')
    item_transactions: list[Item_Transaction] = Relationship(back_populates='items')

class Item_Image_Path(SQLModel, table=True):
    id: int | None = Field(
        default=None, primary_key=True,
    )
    path: str
    item_id: int = Field(foreign_key='item.id')

    item: Item | None = Relationship(back_populates='item_image_paths')

class Transaction(SQLModel, table=True):
    id: str | None = Field(
        default_factory=uuid4, primary_key=True
    )
    name: str = Field(index=True)
    email: str
    phone_number: str
    created_at: str

    item_transactions: list[Item_Transaction] = Relationship(back_populates='transactions')
