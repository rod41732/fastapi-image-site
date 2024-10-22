import os
from typing import Annotated, Any, Sequence
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import sqlalchemy
from sqlmodel import col, select
from app.models import (
    Artwork,
    ArtworkDetailed,
    ArtworkPublic,
    ArtworkUpdate,
    Comment,
    CommentCreate,
    CommentPublic,
    User,
)
from constants import UPLOAD_DIR
from libs.common import ErrorDetail, MessageResponse
from libs.db import SessionDep
from libs.html import CSS_BASE, page_layout
from libs.upload import save_file
from libs.dependencies import CurrentUser, CurrentUserOrNone
from PIL import Image
from sqlalchemy.orm import joinedload
import sqlalchemy.exc
import htpy as h


router = APIRouter()


def _list_artworks_base(db: SessionDep) -> Sequence[Artwork]:
    # TODO: https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html
    images = db.exec(
        select(Artwork)
        .options(joinedload(Artwork.author))
        .order_by(col(Artwork.created_at).desc())
    ).all()
    return images


@router.get("/gallery", response_model=list[ArtworkPublic])
def list_artworks(artworks: Annotated[Sequence[Artwork], Depends(_list_artworks_base)]):
    """List all artworks"""
    return artworks


def _render_artworks(artworks: Sequence[Artwork], *, title="Artworks"):
    return h.html[
        h.head[CSS_BASE],
        h.body()[
            h.div(".container")[
                h.h1[title],
                h.div(
                    style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));",
                )[
                    (
                        h.div(style="padding: 8px")[
                            h.img(
                                src=f"/uploads/{artwork.path}",
                                style="width: 100%; aspect-ratio: 16/9; object-fit: cover; padding: 2px; border: 2px solid red;",
                            ),
                            h.a(
                                href=f"/artworks/{artwork.id}.html",
                                style="color: unset",
                            )[
                                h.p(style="padding-bottom: 8px; font-weight: bold;")[
                                    f"{artwork.name} - #{artwork.id}"
                                ],
                                h.p[artwork.description],
                                h.p(style="opacity: 0.75")[
                                    f"{artwork.created_at.strftime("%b %d, %Y")} - {artwork.author and artwork.author.username}"
                                ],
                            ],
                        ]
                        for artwork in artworks
                    )
                ],
            ]
        ],
    ]


@router.get("/gallery.html", response_class=HTMLResponse, include_in_schema=False)
def list_artworks_html(
    artworks: Annotated[Sequence[Artwork], Depends(_list_artworks_base)],
    user: CurrentUserOrNone,
):
    """List artwork HTML page"""
    return HTMLResponse(
        page_layout(
            user=user,
            body=h.div(style="padding: 16px 24px")[
                _render_artworks(artworks, title="Gallery")
            ],
        )
    )


class UploadArtworkForm(BaseModel):
    name: str
    description: str
    image: UploadFile


@router.post("/upload", response_model=ArtworkPublic)
def upload_artwork(
    form: Annotated[UploadArtworkForm, Form(media_type="multipart/form-data")],
    user: CurrentUser,
    db: SessionDep,
):
    """Upload a new artwork"""
    content_type = form.image.content_type
    if not content_type or not content_type.startswith("image"):
        raise HTTPException(status_code=400, detail="Expected image")

    file_size = form.image.size
    if not file_size:
        raise HTTPException(status_code=400, detail="Cannot determine size of file")

    user_uploads_folder = os.path.join(UPLOAD_DIR, "user-uploads")
    os.makedirs(user_uploads_folder, exist_ok=True)

    save_path = save_file(form.image, user_uploads_folder)
    relpath = os.path.relpath(save_path, start=UPLOAD_DIR)
    if not save_path.startswith(UPLOAD_DIR):
        raise AssertionError(
            f"File saved in '{save_path}' ({relpath}) which is outside upload dir '{UPLOAD_DIR}'"
        )

    with Image.open(save_path) as im:
        width = im.width
        height = im.height

    artwork = Artwork(
        name=form.name,
        description=form.description,
        path=relpath,
        author=user,
        width=width,
        height=height,
        file_size=form.image.size or -1,
    )

    db.add(artwork)
    db.commit()
    db.refresh(artwork)

    return artwork


@router.put(
    "/{artwork_id}",
    response_model=ArtworkPublic,
    responses={
        404: {"model": ErrorDetail},
        403: {"model": ErrorDetail},
    },
)
def update_artwork(
    artwork_id: int, user: CurrentUser, db: SessionDep, update: ArtworkUpdate
):
    """Update specified artwork owned by current user"""
    try:
        artwork = db.exec(select(Artwork).where(Artwork.id == id)).one()
    except sqlalchemy.exc.NoResultFound:
        raise HTTPException(status_code=404, detail="Artwork not found")

    if artwork.author_id != user.id:
        raise HTTPException(status_code=403, detail="Artwork not owned")

    artwork.sqlmodel_update(update.model_dump(exclude_unset=True))
    db.add(artwork)
    db.commit()

    return artwork


@router.delete(
    "/{artwork_id}",
    responses={
        404: {"model": ErrorDetail},
        403: {"model": ErrorDetail},
    },
)
def delete_artwork(
    artwork_id: int, user: CurrentUser, db: SessionDep
) -> MessageResponse:
    """Delete specified artwork owned by current user"""
    try:
        artwork = db.exec(select(Artwork).where(Artwork.id == id)).one()
    except sqlalchemy.exc.NoResultFound:
        raise HTTPException(status_code=404, detail="Artwork not found")

    if artwork.author_id != user.id:
        raise HTTPException(status_code=403, detail="Artwork not owned")

    db.delete(artwork)
    db.commit()

    return MessageResponse(message="Deleted Artwork")


def _get_user_artworks(db: SessionDep, user: CurrentUser) -> Sequence[Artwork]:
    artworks = db.exec(
        select(Artwork)
        .where(Artwork.author_id == user.id)
        .options(joinedload(Artwork.author))
        .order_by(col(Artwork.created_at).desc())
    ).all()
    return artworks


@router.get("/mine", response_model=list[ArtworkPublic])
def list_my_artworks(artworks: Annotated[Any, Depends(_get_user_artworks)]):
    """List all artworks by current user"""
    return artworks


@router.get("/mine.html", response_class=HTMLResponse, include_in_schema=False)
def list_my_artworks_html(
    artworks: Annotated[Any, Depends(_get_user_artworks)], user: CurrentUser
):
    """Display all artworks by current user"""
    return HTMLResponse(
        page_layout(
            user=user,
            body=h.div(style="padding: 16px 24px")[
                _render_artworks(artworks, title=f"{user.username}: My Artworks")
            ],
        )
    )


def _detailed_artwork_base(artwork_id: int, db: SessionDep):
    try:
        artwork = (
            db.exec(
                select(Artwork)
                .options(joinedload(Artwork.author), joinedload(Artwork.comments))
                .where(Artwork.id == artwork_id)
                # .options(joinedload(Artwork.comments))
            ).unique()  # must call unique when join with many-to-one
        ).one()
        print("-- result", artwork)
    except sqlalchemy.exc.NoResultFound:
        raise HTTPException(status_code=404, detail="Artwork not found")

    return artwork


def _render_comment(comment: Comment, *, user: User | None):
    """Render HTML for single comment

    - user: used to determine whether comment is delete-able
    """
    return h.div(style="margin: 8px; 16px; background: #e1e1e1; padding: 8px")[
        h.div(style="font-weight: bold")[comment.author and comment.author.username],
        h.div[comment.text],
        h.div(style="opacity: 0.75; font-size: 0.75em;")[
            comment.created_at.strftime("%b %d, %Y")
        ],
        user and comment.author_id == user.id and h.button["delete"],
    ]


@router.get("/{artwork_id}.html", response_class=HTMLResponse, include_in_schema=False)
def detailed_artwork_page(
    detailed_artwork: Annotated[Artwork, Depends(_detailed_artwork_base)],
    artwork_id: int,
    user: CurrentUserOrNone,
):
    author = detailed_artwork.author

    return HTMLResponse(
        page_layout(
            user=user,
            body=[
                h.div(style="padding: 16px 24px;")[
                    h.h1[
                        f"Viewing Artwork {detailed_artwork.name} #{detailed_artwork.id}"
                    ],
                    h.img(
                        src="/uploads/" + detailed_artwork.path,
                        style="width: 100%; max-width: 768px; aspect-ratio: 16/9; object-fit: cover;",
                    ),
                    h.h2[detailed_artwork.name],
                    h.p(style="font-weight: bold")[
                        f"posted by {author.username if author else '[deleted user]'} at {detailed_artwork.created_at.strftime('%b %d, %Y')}"
                    ],
                    h.p[detailed_artwork.description],
                    h.hr,
                    h.h3["Comments"],
                    user
                    and [
                        h.form(
                            style="margin: 8px; 16px; background: #e1e1e1; padding: 8px",
                            hx_ext="json-enc",
                            hx_post=f"/artworks/{artwork_id}/comments.html",
                            hx_swap="afterend",
                            hx_disabled_elt="find button",
                        )[
                            h.h4[f"Comment as {user.username}"],
                            h.textarea(name="text", rows=5, cols=80),
                            h.br,
                            h.button(type="submit")["Comment"],
                        ],
                    ],
                    [
                        _render_comment(comment, user=user)
                        for comment in sorted(
                            detailed_artwork.comments,
                            key=lambda comment: -comment.created_at.timestamp(),
                        )
                    ],
                ]
            ],
        )
    )


@router.get("/{artwork_id}", response_model=ArtworkDetailed)
def get_detailed_artwork(
    detailed_artwork: Annotated[Artwork, Depends(_detailed_artwork_base)]
):
    return detailed_artwork


def _comment_on_artwork_base(
    artwork_id: int, user: CurrentUser, comment_details: CommentCreate, db: SessionDep
) -> Comment:
    """Create comment on artwork, returnin created comment"""
    try:
        db.exec(select(Artwork).where(Artwork.id == artwork_id))
    except sqlalchemy.exc.NoResultFound:
        raise HTTPException(status_code=404, detail="Artwork not found")

    created_comment = Comment(
        author_id=user.id,
        artwork_id=artwork_id,
        text=comment_details.text,
    )
    db.add(created_comment)
    db.commit()
    return created_comment


@router.post("/{artwork_id}/comments", response_model=CommentPublic)
def comment_on_artwork(
    created_comment: Annotated[Comment, Depends(_comment_on_artwork_base)],
):
    """Create comment on artwork"""
    return created_comment


@router.post(
    "/{artwork_id}/comments.html", response_class=HTMLResponse, include_in_schema=False
)
def comment_on_artwork_html(
    created_comment: Annotated[Comment, Depends(_comment_on_artwork_base)],
    user: CurrentUser,
):
    """Create comment on artwork"""
    return HTMLResponse(_render_comment(created_comment, user=user))


@router.get("/{artwork_id}/comments", response_model=list[CommentPublic])
def list_artwork_comments(artwork_id: int, db: SessionDep):
    """list comments on artwork"""
    comments = db.exec(
        select(Comment)
        .where(Comment.artwork_id == artwork_id)
        .options(
            joinedload(Comment.artwork).joinedload(Artwork.author),
            joinedload(Comment.author),
        )
        .order_by(col(Comment.created_at).desc())
    )
    return comments


@router.delete("/i/comments/{comment_id}")
def delete_artwork_comment(
    comment_id: int, user: CurrentUser, db: SessionDep
) -> MessageResponse:
    """Delete user's comment on artwork"""
    try:
        comment = db.exec(select(Comment).where(Comment.id == comment_id)).one()
    except sqlalchemy.exc.NoResultFound:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.author_id != user.id:
        raise HTTPException(status_code=403, detail="Comment not owned by you")

    db.delete(comment)
    db.commit()

    return MessageResponse(message="Deleted comment")
