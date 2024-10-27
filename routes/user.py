import json
import random
from typing import Annotated, Any, Sequence
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from markupsafe import Markup
from pydantic import BaseModel
from sqlalchemy.orm import joinedload
import sqlalchemy.exc
import htpy as h
from sqlmodel import col, select
from routes.artworks.view import _render_artworks

from app.models import (
    Artwork,
    ArtworkPublic,
    User,
    UserCreate,
    UserFavoriteArtwork,
    UserPublic,
)
from libs.common import ErrorDetail, MessageResponse
from libs.db import SessionDep
from libs.dependencies import CurrentUser, CurrentUserOrNone
from libs.html import make_redirect_response, page_layout
from libs.password import PasswordValidationError, hash_password, verify_password

router = APIRouter()


def _register_base(user: UserCreate, session: SessionDep) -> User:
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


@router.post(
    "/register",
    response_model=UserPublic,
    responses={400: {"model": ErrorDetail}},
)
def register_user(
    registered_user: Annotated[User, Depends(_register_base)], request: Request
):
    request.session.clear()
    request.session["user_id"] = registered_user.id
    request.session["user_username"] = registered_user.username
    return registered_user


@router.get(
    "/register.html",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def register_page(user: CurrentUserOrNone):
    return str(
        page_layout(
            user=user,
            body=[
                h.div(
                    style="width: 100%; max-width: 480px; background: #eeeeee; margin: 0 auto; padding: 12px 24px;"
                )[
                    h.h1(style="text-align: center")["Register"],
                    h.style[
                        Markup(
                            """
                        .register-form {
                            padding: 16px 32px;
                        }

                        .register-form > * { 
                            margin: 8px 0;
                            display: block;
                        }
                    """
                        )
                    ],
                    h.form(
                        ".register-form",
                        hx_trigger="submit",
                        hx_target="body",
                        hx_post="/user/register.html",
                        hx_ext="json-enc",
                    )[
                        h.label["username"],
                        h.input(name="username"),
                        h.label["password"],
                        h.input(name="password", type="password"),
                        h.label["email"],
                        h.input(name="email", type="email"),
                        h.button(type="submit")["Register"],
                        h.a(href="/user/login.html")["Already have an account? Login"],
                    ],
                ]
            ],
        )
    )


@router.post(
    "/register.html",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def register_form(
    registered_user: Annotated[User, Depends(_register_base)], request: Request
):
    request.session.clear()
    request.session["user_id"] = registered_user.id
    request.session["user_username"] = registered_user.username
    return make_redirect_response("/")


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
    session.commit()

    print("almost return")
    return user


class LoginDto(BaseModel):
    username: str
    password: str


def _login_user(login: LoginDto, session: SessionDep, request: Request) -> User:
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


@router.post(
    "/login", responses={401: {"model": ErrorDetail}}, response_model=UserPublic
)
def login_user(logged_in_user: Annotated[Any, Depends(_login_user)]):
    """Login, return logged in user"""
    return login_user


@router.post(
    "/login.html",
    responses={401: {"model": ErrorDetail}},
    response_class=HTMLResponse,
    include_in_schema=False,
)
def login_user_form(user: Annotated[User, Depends(_login_user)]):
    return make_redirect_response("/")


@router.get(
    "/login.html",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def login_page(user: CurrentUserOrNone):
    return str(
        page_layout(
            user=user,
            body=[
                h.div(
                    style="width: 100%; max-width: 480px; background: #eeeeee; margin: 0 auto; padding: 12px 24px;"
                )[
                    h.h1(style="text-align: center")["Login"],
                    h.style[
                        Markup(
                            """
                        .login-form {
                            padding: 16px 32px;
                        }

                        .login-form > * { 
                            margin: 8px 0;
                            display: block;
                        }
                    """
                        )
                    ],
                    h.form(
                        ".login-form",
                        hx_trigger="submit",
                        hx_post="/user/login.html",
                        hx_ext="json-enc",
                    )[
                        h.label["username"],
                        h.input(name="username"),
                        h.label["password"],
                        h.input(name="password", type="password"),
                        h.button(type="submit")["Login"],
                        h.a(href="/user/register.html")[
                            "Don't have an account? Register"
                        ],
                    ],
                ]
            ],
        )
    )


def _logout_base(request: Request) -> MessageResponse:
    session = request.session
    if "user_id" not in session:
        raise HTTPException(status_code=401, detail="Not logged in")

    session.clear()
    return MessageResponse(message="Logged out")


@router.post("/logout")
def logout_user(
    logout_result: Annotated[MessageResponse, Depends(_logout_base)],
    request: Request,
) -> MessageResponse:
    """Logout user"""
    return logout_result


@router.post(
    "/logout.html",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def logout_user_html(logout_result: Annotated[MessageResponse, Depends(_logout_base)]):
    """Logout user"""
    return make_redirect_response("/")


@router.post("/me", response_model=UserPublic)
def get_current_user(user: CurrentUser):
    return user


def _get_user_by_id_base(user_id: int, db: SessionDep):
    """return user by ID"""
    try:
        user = db.exec(select(User).where(User.id == user_id)).one()
        return user
    except sqlalchemy.exc.NoResultFound:
        raise HTTPException(status_code=404, detail="User not found")


@router.get("/{user_id}.html", response_class=HTMLResponse, include_in_schema=False)
def user_profile_page(
    *,
    user: Annotated[User, Depends(_get_user_by_id_base)],
    current_user: CurrentUserOrNone,
    user_id: int,
    tab: str = "artworks",
    db: SessionDep,
):
    sub_page = None
    if tab == "artworks":
        sub_page = h.render_node(
            [
                _render_artworks(_list_user_artworks_base(user_id=user_id, db=db)),
            ]
        )
    elif tab == "favorites":
        sub_page = _render_artworks(
            _list_user_favorite_artworks_base(user_id=user_id, db=db)
        )

    initial_state = json.dumps({"tab": tab})

    return HTMLResponse(
        page_layout(
            user=current_user,
            body=h.div(
                style="padding: 16px 24px", id="profile-app", x_data=initial_state
            )[
                h.div(style="margin-bottom: 8px")[
                    h.h1[f"{user.username}'s Profile"],
                    h.p[f"User ID: #{user.id}"],
                ],
                h.style[
                    Markup(
                        """
                    .profile-header {
                        padding: 8px 12px;
                        background: #e1e1e1;
                    }

                    .profile-header > a {
                        display: inline-block;
                        margin: 0px 12px;
                        font-weight: bold;
                        padding: 0.25em 0.5em;
                    }

                    .profile-header > a.active { 
                        background: grey;
                        color: white;
                    }
                """
                    )
                ],
                h.p(class_="profile-header", hx_boost="true")[
                    h.a(
                        {
                            "x-bind:class": 'tab == "artworks" ? "active": ""',
                            "x-on:htmx:after-request": "if ($event.detail.successful) tab = 'artworks'",
                        },
                        hx_get=f"/user/{user_id}/artworks.phtml",
                        hx_push_url=f"/user/{user_id}.html?tab=artworks",
                        hx_target="#artworks-list",
                    )["Artworks"],
                    h.a(
                        {
                            "x-bind:class": 'tab == "favorites" ? "active": ""',
                            "x-on:htmx:after-request": "if ($event.detail.successful) tab = 'favorites'",
                        },
                        hx_get=f"/user/{user_id}/favorite-artworks.phtml",
                        hx_push_url=f"/user/{user_id}.html?tab=favorites",
                        hx_target="#artworks-list",
                    )["Favorites"],
                    # h.p(x_text="a")["loading..."],
                ],
                h.div(
                    id="artworks-list",
                )[sub_page],
            ],
        )
    )


@router.get("/{user_id}", response_model=UserPublic)
def get_user_by_id(user: Annotated[User, Depends(_get_user_by_id_base)]):
    """return user by ID"""
    return user


def _list_user_artworks_base(user_id: int, db: SessionDep) -> Sequence[Artwork]:
    """list user artworks"""
    user_artworks = db.exec(
        select(Artwork)
        .options(
            joinedload(Artwork.author),
        )
        .where(
            Artwork.author_id == user_id,
        )
        .order_by(col(Artwork.created_at).desc())
    ).all()
    return user_artworks


@router.get("/{user_id}/artworks", response_model=list[ArtworkPublic])
def list_user_artworks(
    user_artworks: Annotated[Sequence[Artwork], Depends(_list_user_artworks_base)],
):
    """list user artworks"""
    return user_artworks


@router.get(
    "/{user_id}/artworks.phtml", response_class=HTMLResponse, include_in_schema=False
)
def list_user_artworks_partial_html(
    user_artworks: Annotated[Sequence[Artwork], Depends(_list_user_artworks_base)],
):
    """partial HTML response for listing artworks"""
    return HTMLResponse(_render_artworks(user_artworks))


def _list_user_favorite_artworks_base(user_id: int, db: SessionDep) -> list[Artwork]:
    """return list of artworks favorited by user"""
    favorites = db.exec(
        select(UserFavoriteArtwork)
        .options(
            joinedload(UserFavoriteArtwork.artwork).joinedload(Artwork.author),
        )
        .where(UserFavoriteArtwork.user_id == user_id)
        .order_by(col(UserFavoriteArtwork.favorited_at).desc())
    )
    favorited_artworks = [favorite.artwork for favorite in favorites]
    return favorited_artworks


@router.get("/{user_id}/favorite-artworks", response_model=list[ArtworkPublic])
def list_user_favorite_artworks(
    user_favorite_artworks: Annotated[
        list[Artwork], Depends(_list_user_favorite_artworks_base)
    ],
):
    """List artworks favorited by user"""
    return user_favorite_artworks


@router.get(
    "/{user_id}/favorite-artworks.phtml",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def list_user_favorite_artworks_partial_html(
    user_favorite_artworks: Annotated[
        list[Artwork], Depends(_list_user_favorite_artworks_base)
    ],
):
    return HTMLResponse(_render_artworks(user_favorite_artworks))
