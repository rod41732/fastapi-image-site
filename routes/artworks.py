from fastapi import APIRouter
from sqlmodel import col, select
from app.models import Artwork
from libs.db import SessionDep


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


# @router.post("")
