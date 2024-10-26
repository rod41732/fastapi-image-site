from typing import Annotated, Any, Sequence
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
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
    UserFavoriteArtwork,
    UserFavoriteArtworkPublic,
)
from libs.common import ErrorDetail, MessageResponse
from libs.db import SessionDep
from libs.html import page_layout
from libs.dependencies import CurrentUser, CurrentUserOrNone
from sqlalchemy.orm import joinedload
import sqlalchemy.exc
import htpy as h
from .view import _render_artworks


def mount_apis(router: APIRouter):
    @router.get("/favorites", response_model=list[ArtworkPublic])
    def list_favorite_artworks(user: CurrentUser, db: SessionDep):
        """List favorited artworks, ordered by time"""
        favorites = db.exec(
            select(UserFavoriteArtwork)
            .options(
                joinedload(UserFavoriteArtwork.artwork).joinedload(Artwork.author),
            )
            .where(
                UserFavoriteArtwork.user_id == user.id,
            )
            .order_by(col(UserFavoriteArtwork.favorited_at).desc())
        )
        favorited_artworks = [favorite.artwork for favorite in favorites]
        return favorited_artworks

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
                    _render_artworks(
                        artworks,
                        title=f"{user.username}: My Artworks",
                        show_upload=True,
                    )
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
        return h.div(
            style="",
            class_="artwork-comment",
        )[
            h.div(style="font-weight: bold")[
                comment.author and comment.author.username
            ],
            h.div[comment.text],
            h.div(style="opacity: 0.75; font-size: 0.75em;")[
                comment.created_at.strftime("%b %d, %Y")
            ],
            user
            and comment.author_id == user.id
            and h.button(
                hx_delete=f"/artworks/i/comments/{comment.id}",
                hx_swap="delete swap:1s",
                hx_target="closest .artwork-comment",
                hx_confirm="Delete this comment?",
            )["delete"],
        ]

    @router.get(
        "/{artwork_id}.html", response_class=HTMLResponse, include_in_schema=False
    )
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
                                hx_on_htmx_after_request="if (event.detail.successful) this.reset(); else alert('Comment failed')",
                            )[
                                h.h4[f"Comment as {user.username}"],
                                h.textarea(
                                    name="text",
                                    rows=5,
                                    style="width: 100%; max-width: 768px;",
                                ),
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
        detailed_artwork: Annotated[Artwork, Depends(_detailed_artwork_base)],
    ):
        return detailed_artwork

    def _comment_on_artwork_base(
        artwork_id: int,
        user: CurrentUser,
        comment_details: CommentCreate,
        db: SessionDep,
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
        "/{artwork_id}/comments.html",
        response_class=HTMLResponse,
        include_in_schema=False,
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

    @router.post("/{artwork_id}/favorite", response_model=UserFavoriteArtworkPublic)
    def favorite_artwork(user: CurrentUser, artwork_id: int, db: SessionDep):
        """Favorite specified artwork"""
        artwork_exist = db.query(
            select(Artwork).where(Artwork.id == artwork_id).exists()
        ).scalar()
        if not artwork_exist:
            raise HTTPException(
                status_code=404, detail=f"Artwork {artwork_id} does not exist"
            )

        favorite = UserFavoriteArtwork(user_id=user.id, artwork_id=artwork_id)  # type: ignore
        try:
            db.add(favorite)
            db.commit()
        except sqlalchemy.exc.IntegrityError:
            raise HTTPException(
                status_code=409, detail=f"Artwork {artwork_id} already favorited"
            )
        return favorite

    @router.delete("/{artwork_id}/favorite", response_model=UserFavoriteArtworkPublic)
    def unfavorite_artwork(user: CurrentUser, artwork_id: int, db: SessionDep):
        """Unfavorite specified artwork"""
        try:
            favorite = db.exec(
                select(UserFavoriteArtwork).where(
                    UserFavoriteArtwork.artwork_id == artwork_id,
                    UserFavoriteArtwork.user_id == user.id,
                )
            ).one()
        except sqlalchemy.exc.NoResultFound:
            raise HTTPException(
                status_code=404,
                detail=f"Artwork {artwork_id} is not favorited or does not exist",
            )

        delete_count = (
            db.query(UserFavoriteArtwork)
            .where(
                col(UserFavoriteArtwork.artwork_id) == artwork_id,
                col(UserFavoriteArtwork.user_id) == user.id,
            )
            .delete()
        )
        assert delete_count == 1

        return favorite
