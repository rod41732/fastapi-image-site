from typing import Annotated, Sequence
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlmodel import col, select
from app.models import (
    Artwork,
    ArtworkPublic,
)
from libs.db import SessionDep
from libs.html import page_layout
from libs.dependencies import CurrentUserOrNone
from sqlalchemy.orm import joinedload
import htpy as h
from .view import _render_artworks


def mount_apis(router: APIRouter):
    def _list_artworks_base(db: SessionDep) -> Sequence[Artwork]:
        # TODO: https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html
        images = db.exec(
            select(Artwork)
            .options(joinedload(Artwork.author))  # type: ignore
            .order_by(col(Artwork.created_at).desc())
        ).all()
        return images

    @router.get("/gallery", response_model=list[ArtworkPublic])
    def list_artworks(
        artworks: Annotated[Sequence[Artwork], Depends(_list_artworks_base)]
    ):
        """List all artworks"""
        return artworks

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
