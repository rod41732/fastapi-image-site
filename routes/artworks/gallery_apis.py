from operator import or_
from typing import Annotated, Sequence
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from markupsafe import Markup
from sqlmodel import col, select
from app.models import (
    Artwork,
    ArtworkPublic,
)
from libs.db import SessionDep
from libs.html import page_layout
from libs.dependencies import CurrentUserOrNone
from sqlalchemy.orm import joinedload
from sqlalchemy import or_
import htpy as h
from .view import _render_artworks


def mount_apis(router: APIRouter):
    def _list_artworks_base(db: SessionDep, query: str = "") -> Sequence[Artwork]:
        images = db.exec(
            select(Artwork)
            .where(
                col(Artwork.name).icontains(query)
                | col(Artwork.description).icontains(query)
            )
            .options(joinedload(Artwork.author))  # type: ignore
            .order_by(col(Artwork.created_at).desc())
        ).all()

        return images

    @router.get("/gallery", response_model=list[ArtworkPublic])
    def list_artworks(
        artworks: Annotated[Sequence[Artwork], Depends(_list_artworks_base)],
    ):
        """List all artworks"""
        return artworks

    def _make_result_title(query: str, *, is_for_swap: bool = False):
        return (
            h.div(
                id="search-results-title", hx_swap_oob="true" if is_for_swap else False
            )[
                h.p[
                    (
                        "Showing all artworks"
                        if not query
                        else f'Searching for "{query}"'
                    )
                ]
            ],
        )

    @router.get("/gallery.phtml")
    def artworks_gallery_partial_page(
        artworks: Annotated[Sequence[Artwork], Depends(_list_artworks_base)],
        query: str = "",
    ):
        """Return rendered HTML for search result, this is similar to below but without site structure"""
        return HTMLResponse(
            h.render_node(
                [
                    (
                        _render_artworks(artworks)
                        if artworks
                        else h.p(style="text-align: center; padding: 16px 24px;")[
                            "No result found for ",
                            h.span(style="font-weight: bold")[query],
                        ]
                    ),
                    _make_result_title(query, is_for_swap=True),
                ]
            )
        )

    @router.get("/gallery.html", response_class=HTMLResponse, include_in_schema=False)
    def artworks_gallery_page(
        artworks: Annotated[Sequence[Artwork], Depends(_list_artworks_base)],
        user: CurrentUserOrNone,
        query: str = "",
    ):
        """List artwork HTML page"""

        return HTMLResponse(
            page_layout(
                user=user,
                body=h.div(style="padding: 16px 24px")[
                    h.h1["Artworks"],
                    h.style[
                        Markup(
                            """
                    .artworks-filter-row {
                        display: flex;
                        align-items: center;
                        gap: 0px 8px;
                        flex-wrap: wrap;
                    }

                    """
                        )
                    ],
                    h.div(class_="artworks-filter-row")[
                        _make_result_title(query),
                        h.div(style="flex: 1"),
                        h.form(
                            # -- normal form
                            # method="GET",
                            # -- htmx form
                            hx_get="/artworks/gallery.phtml",
                            hx_swap="innerhtml",
                            hx_target="#artworks-result",
                            hx_on_htmx_after_request="console.log(event); if (event.detail.successful) history.pushState('', '', event.detail.pathInfo.responsePath.replace('.phtml', '.html'))",
                        )[
                            h.input(
                                value=query,
                                name="query",
                                placeholder="Search in name, description",
                                style="margin: 8px; min-width: 200px; max-width: 400px; width: 33vw;",
                            ),
                            h.button(style="margin: 8px")["Search"],
                        ],
                    ],
                    (
                        h.div("#artworks-result")[
                            (
                                _render_artworks(artworks)
                                if artworks
                                else h.p(
                                    style="text-align: center; padding: 16px 24px;"
                                )[
                                    "No result found for ",
                                    h.span(style="font-weight: bold")[query],
                                ]
                            )
                        ]
                    ),
                ],
            )
        )
