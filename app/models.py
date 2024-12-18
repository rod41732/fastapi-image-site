import datetime
from typing import Annotated, Union

from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel


def _now():
    return datetime.datetime.fromtimestamp(
        datetime.datetime.now().timestamp(), datetime.UTC
    )


class UserFavoriteArtwork(SQLModel, table=True):
    user_id: Annotated[int, Field(foreign_key="user.id", primary_key=True)]
    user: "User" = Relationship()
    artwork_id: Annotated[int, Field(foreign_key="artwork.id", primary_key=True)]
    artwork: "Artwork" = Relationship()
    favorited_at: datetime.datetime = Field(default_factory=_now)


class UserFavoriteArtworkPublic(BaseModel):
    user: "UserPublic"
    artwork: "ArtworkPublic"
    favorited_at: datetime.datetime


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
    comments: list[Union["Comment", None]] = Relationship(back_populates="author")
    favorite_artworks: list["Artwork"] = Relationship(
        back_populates="favoriting_users",
        link_model=UserFavoriteArtwork,
        sa_relationship_kwargs={"overlaps": "user,artwork"},
    )

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
    favoriting_users: list["User"] = Relationship(
        back_populates="favorite_artworks",
        link_model=UserFavoriteArtwork,
        sa_relationship_kwargs={"overlaps": "artwork,user"},
    )

    comments: list["Comment"] = Relationship(back_populates="artwork")


class ArtworkPublic(ArtworkBase):
    """Public field of 'Artwork' usually returned in listing or as related object"""

    id: int
    author: UserPublic | None


class ArtworkUpdate(BaseModel):
    name: str
    description: str


class Comment(SQLModel, table=True):
    id: Annotated[int | None, Field(primary_key=True)] = None
    text: Annotated[str, Field()]
    created_at: datetime.datetime = Field(default_factory=_now)

    artwork_id: Annotated[int | None, Field(foreign_key="artwork.id")] = None
    artwork: Artwork | None = Relationship(back_populates="comments")

    author_id: Annotated[int | None, Field(foreign_key="user.id")] = None
    author: User | None = Relationship(back_populates="comments")


class CommentCreate(BaseModel):
    text: Annotated[str, Field()]


class CommentPublic(BaseModel):
    id: int
    text: str
    created_at: datetime.datetime
    artwork: ArtworkPublic | None
    author: UserPublic | None


class ArtworkDetailed(ArtworkBase):
    """Detailed Artwork model"""

    id: int
    author: UserPublic | None
    comments: list[CommentPublic]
