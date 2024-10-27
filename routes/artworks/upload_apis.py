import os
from typing import Annotated
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from app.models import (
    Artwork,
    ArtworkPublic,
)
from constants import UPLOAD_DIR
from libs.db import SessionDep
from libs.upload import save_file
from libs.dependencies import CurrentUser
from PIL import Image
from .view import _render_artwork


class UploadArtworkForm(BaseModel):
    name: str
    description: str
    image: UploadFile


def mount_apis(router: APIRouter):
    def _upload_artwork_base(
        form: Annotated[UploadArtworkForm, Form(media_type="multipart/form-data")],
        user: CurrentUser,
        db: SessionDep,
    ) -> Artwork:
        """Upload a new artwork, return created artwork"""
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

    @router.post("/upload", response_model=ArtworkPublic)
    def upload_artwork(
        created_artwork: Annotated[Artwork, Depends(_upload_artwork_base)],
    ):
        """Upload a new artwork, return created artwork"""
        return created_artwork

    @router.post("/upload.html", response_class=HTMLResponse, include_in_schema=False)
    def upload_artwork_html(
        created_artwork: Annotated[Artwork, Depends(_upload_artwork_base)],
    ):
        """Upload a new artwork, return created artwork"""
        return str(_render_artwork(created_artwork, extra_classes=["new"]))
