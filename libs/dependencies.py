from typing import Annotated
from fastapi import Depends, HTTPException, Request
import sqlalchemy.exc
from sqlmodel import col, select
from app.models import User
from libs.db import SessionDep


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


def get_current_user_or_none(request: Request, db: SessionDep) -> User | None:
    """Return current user, or none if not logged in"""
    try:
        return get_current_user(request=request, db=db)
    except HTTPException:
        return None


CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentUserOrNone = Annotated[User | None, Depends(get_current_user_or_none)]
