from turtle import back
from typing import Annotated, Union
from fastapi import Depends
from sqlalchemy import create_engine
from sqlmodel import Relationship, SQLModel, Session, Field


sqlite_filename = "database.db"
sqlite_url = f"sqlite:///{sqlite_filename}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        print("Get session called")
        yield session
        print("after yielding")
        session.commit()


SessionDep = Annotated[Session, Depends(get_session)]
