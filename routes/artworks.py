import os
from typing import Annotated
from fastapi import APIRouter, Form, HTTPException, UploadFile
from pydantic import BaseModel
import sqlalchemy
from sqlmodel import col, select
from app.models import Artwork, ArtworkPublic, ArtworkUpdate
from constants import UPLOAD_DIR
from libs.common import ErrorDetail, MessageResponse
from libs.db import SessionDep
from libs.upload import save_file
from libs.dependencies import CurrentUser
from PIL import Image
from sqlalchemy.orm import joinedload
import sqlalchemy.exc


router = APIRouter()


@router.get("/gallery", response_model=list[ArtworkPublic])
def list_artworks(db: SessionDep):
    """List all artworks"""
    # TODO: https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html
    images = db.exec(
        select(Artwork)
        .options(joinedload(Artwork.author))
        .order_by(col(Artwork.created_at).desc())
    ).all()
    return images


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


@router.get("/mine", response_model=list[ArtworkPublic])
def list_my_artworks(user: CurrentUser, db: SessionDep):
    """List all artworks by current user"""
    artworks = db.exec(
        select(Artwork)
        .where(Artwork.author_id == user.id)
        .options(joinedload(Artwork.author))
        .order_by(col(Artwork.created_at).desc())
    ).all()
    return artworks
