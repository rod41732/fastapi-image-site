import random
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import sqlalchemy
import sqlalchemy.exc
from sqlmodel import select

from app.models import User, UserCreate, UserPublic
from libs.common import ErrorDetail, MessageResponse
from libs.db import SessionDep
from libs.dependencies import CurrentUser
from libs.password import PasswordValidationError, hash_password, verify_password

router = APIRouter()


@router.post(
    "/register",
    response_model=UserPublic,
    responses={400: {"model": ErrorDetail}},
)
def register_user(user: UserCreate, session: SessionDep):
    existing_user = session.exec(
        select(User).where(User.username == user.username)
    ).first()

    if existing_user:
        if not existing_user.email_confirmed:
            session.delete(existing_user)
            session.flush()  # need to flush
            print(f">> deleted unconfirmed user of {user.username}")
        else:
            # very raw
            # return JSONResponse(
            #     status_code=400,
            #     # content=jsonable_encoder(ErrorDetail(detail="Username already exist")),
            #     # NOTE: data must be JSON compatiable
            #     content=jsonable_encoder(ErrorDetail(detail="Username already exists")),
            # )
            raise HTTPException(status_code=400, detail="Username already exists")

    email_token = str(random.randint(100_000, 999_999))
    print(f">> use this code {email_token} to confirm email for {user.username}")

    user.password = hash_password(user.password)
    db_user = User(
        username=user.username,
        password=user.password,
        email=user.email,
        email_confirmation_token=email_token,
    )

    session.add(db_user)
    session.commit()

    return db_user


@router.get("/email-confirmation", response_model=UserPublic)
def user_email_confirmation(token: str, session: SessionDep):
    """User email confirmation"""
    user = session.exec(
        select(User).where(User.email_confirmation_token == token)
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="Invalid token")
    user.email_confirmation_token = None
    user.email_confirmed = True
    session.add(user)

    print("almost return")
    return user


class LoginDto(BaseModel):
    username: str
    password: str


@router.post(
    "/login", responses={401: {"model": ErrorDetail}}, response_model=UserPublic
)
def login_user(login: LoginDto, session: SessionDep, request: Request):
    try:
        user = session.exec(select(User).where(User.username == login.username)).one()
        request.session["user_id"] = user.id
        request.session["user_username"] = user.username
    except sqlalchemy.exc.NoResultFound:
        print(">> invalid username")
        raise HTTPException(status_code=401, detail="Invalid username or password")
    try:
        verify_password(login.password, user.password)
    except PasswordValidationError:
        print(">> invalid password")
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return user


@router.post("/logout")
def logout_user(request: Request) -> MessageResponse:
    session = request.session
    if "user_id" not in session:
        raise HTTPException(status_code=401, detail="Not logged in")

    session.clear()
    return MessageResponse(message="Logged out")


@router.post("/me", response_model=UserPublic)
def get_current_user(user: CurrentUser):
    return user
