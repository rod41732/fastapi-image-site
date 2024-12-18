from typing import Sequence

import htpy as h

from app.models import (
    Artwork,
)


def _render_artwork(artwork: Artwork, *, extra_classes: list[str] | None = None):
    class_ = " ".join(["artwork"] + (extra_classes or []))
    return h.div(class_=class_)[
        h.a(
            href=f"/artworks/{artwork.id}.html",
            style="color: unset",
        )[
            h.img(
                src=f"/uploads/{artwork.path}",
                style="width: 100%; aspect-ratio: 16/9; object-fit: cover; padding: 2px; border: 2px solid red;",
            ),
        ],
        h.p(style="padding-bottom: 8px; font-weight: bold;")[
            h.a(
                href=f"/artworks/{artwork.id}.html",
                style="color: unset;",
            )[f"{artwork.name} - #{artwork.id}"]
        ],
        h.p[artwork.description],
        h.p(style="opacity: 0.75")[
            f"{artwork.created_at.strftime("%b %d, %Y")}",
            artwork.author
            and [
                h.span[" - "],
                h.a(
                    href=f"/user/{artwork.author.id}.html",
                    style="font-weight: bold; color: unset;",
                )[artwork.author.username],
            ],
        ],
    ]


def _render_artworks(
    artworks: Sequence[Artwork], *, title: str | None = None, show_upload: bool = False
):
    return h.div(".container")[
        title and h.h1[title],
        show_upload
        and h.details(style="margin-bottom: 16px")[
            h.summary["Upload new artwork"],
            h.div(style="padding: 8px 12px; background: #e1e1e1;")[
                h.form(
                    hx_on_htmx_after_request="if (event.detail.successful) this.reset(); else alert('Upload failed')",
                    hx_post="/artworks/upload.html",
                    method="post",
                    class_="upload-artwork-form",
                    hx_swap="afterbegin",
                    hx_target="#artwork-grid",
                    enctype="multipart/form-data",
                )[
                    h.p[
                        h.label["Image",],
                        h.input(type="file", name="image", accept="image/*"),
                    ],
                    h.p[
                        h.label["Name"],
                        h.input(name="name"),
                    ],
                    h.p[
                        h.label["Description"],
                        h.input(name="description"),
                    ],
                    h.p[h.button(type="submit")["Upload"],],
                ],
            ],
        ],
        h.div(
            style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr))",
            id="artwork-grid",
        )[(_render_artwork(artwork) for artwork in artworks)],
    ]
