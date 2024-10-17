from typing import Annotated
from fastapi import Depends, HTTPException, Request
import sqlalchemy.exc
from sqlmodel import col, select
from app.models import User
from libs.db import SessionDep

# __all__ = ["get_current_user", "CurrentUser"]


def get_current_user(request: Request, db: SessionDep) -> User:
    session = request.session
    if "user_id" not in session:
        raise HTTPException(status_code=401, detail="Not logged in")

    user_id = session["user_id"]
    try:
        user = db.exec(select(User).where(col(User.id) == int(user_id))).one()
        return user
    except sqlalchemy.exc.NoResultFound:
        session.clear()
        raise HTTPException(status_code=401, detail="User is deleted")


CurrentUser = Annotated[User, Depends(get_current_user)]
