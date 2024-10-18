import datetime
from typing import Annotated
from pydantic import BaseModel
from sqlalchemy import ClauseElement
import sqlmodel
from typing_extensions import _AnnotatedAlias
from sqlmodel import Relationship, SQLModel, Field
from typing import Annotated
from sqlmodel import SQLModel


def _now():
    return datetime.datetime.fromtimestamp(
        datetime.datetime.now().timestamp(), datetime.UTC
    )


class UserBase(SQLModel):
    username: Annotated[str, Field(index=True, unique=True)]
    email: Annotated[str, Field(unique=True)]


class User(UserBase, table=True):
    """User database model"""

    id: Annotated[int | None, Field(primary_key=True)] = None
    password: Annotated[str, Field(index=True)]

    email_confirmation_token: Annotated[str | None, Field()] = None
    email_confirmed: Annotated[bool, Field()] = False

    artworks: list["Artwork"] = Relationship(back_populates="author")

    created_at: datetime.datetime = Field(default_factory=_now)
    updated_at: datetime.datetime = Field(default_factory=_now)


class UserCreate(UserBase):
    """Create user payload"""

    password: str


class UserPublic(UserBase):
    """Public field for user"""

    id: int


class ArtworkBase(SQLModel):
    name: str
    description: str
    # path: might be relative or absolute depending on backend
    path: str
    file_size: int
    width: int
    height: int

    created_at: datetime.datetime = Field(default_factory=_now)
    updated_at: datetime.datetime = Field(default_factory=_now)


class Artwork(ArtworkBase, table=True):
    id: Annotated[int | None, Field(primary_key=True)] = None

    author_id: Annotated[int | None, Field(index=True, foreign_key="user.id")] = None
    author: User | None = Relationship(back_populates="artworks")


class ArtworkPublic(ArtworkBase):
    id: int
    author: UserPublic | None


class ArtworkUpdate(BaseModel):
    name: str
    description: str
