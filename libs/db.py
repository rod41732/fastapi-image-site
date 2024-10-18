from turtle import back
from typing import Annotated, Union
from fastapi import Depends
from sqlalchemy import create_engine
from sqlmodel import Relationship, SQLModel, Session, Field


# sqlite_filename = "database.db"
db_url = f"postgresql://postgres:postgres@127.0.0.1:5435/image_site"

engine = create_engine(db_url)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
