from typing import Annotated
from fastapi import Depends
from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session, Field


sqlite_filename = "database.db"
sqlite_url = f"sqlite:///{sqlite_filename}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


class UserBase(SQLModel):
    username: Annotated[str, Field(index=True, unique=True)]
    email: Annotated[str, Field(unique=True)]


class User(UserBase, table=True):
    """User database model"""

    id: Annotated[int | None, Field(primary_key=True)] = None
    password: Annotated[str, Field(index=True)]

    email_confirmation_token: Annotated[str | None, Field()] = None
    email_confirmed: Annotated[bool, Field()] = False


class Artwork(UserBase, table=True):
    id: Annotated[int | None, Field(primary_key=True)] = None
    name: str
    description: str
    # path: might be relative or absolute depending on backend
    path: str
    file_size: int
    width: int
    height: int


class UserCreate(UserBase):
    """Create user payload"""

    password: str


class UserPublic(UserBase):
    """Public field for user"""

    id: int


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        print("Get session called")
        yield session
        print("after yielding")
        session.commit()


SessionDep = Annotated[Session, Depends(get_session)]
