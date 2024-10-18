import os
from typing import Annotated
from fastapi import APIRouter, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlmodel import col, select
from app.models import Artwork, ArtworkPublic
from constants import UPLOAD_DIR
from libs.db import SessionDep
from libs.upload import save_file
from libs.dependencies import CurrentUser
from PIL import Image


router = APIRouter()

# @router.post(
#     '/upload'
# )
# def


@router.get("/gallery", response_model=list[Artwork])
def list_artworks(db: SessionDep):
    """List all artworks"""
    images = db.exec(select(Artwork).order_by(col(Artwork.id).desc())).all()
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
) -> Artwork:
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
