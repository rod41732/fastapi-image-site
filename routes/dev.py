import datetime
import logging
import mimetypes
import shutil
from typing import Annotated
import uuid
from fastapi import APIRouter, File, Form, Query, Request, UploadFile
from pydantic import BaseModel
from sqlmodel import SQLModel, col, select

from app.models import User
from constants import UPLOAD_DIR
from libs.db import create_db_and_tables, SessionDep
import os

router = APIRouter()


@router.post("/recreate-table")
def dev_drop_table(session: SessionDep):
    SQLModel.metadata.drop_all(session.connection())
    create_db_and_tables()
    return {"details": "Dropped and re-created all tables"}


@router.post("/drop-table")
def dev_drop_table_only(session: SessionDep):
    SQLModel.metadata.drop_all(session.connection())
    # create_db_and_tables()
    return {"details": "Dropped tables"}


@router.post("/list-users", response_model=list[User])
def dev_list_users(session: SessionDep):
    return session.exec(select(User).order_by(col(User.id).desc())).all()


@router.delete("/delete-user/{id}")
def dev_delete_user(id: int, session: SessionDep):
    delete_count = (
        session.query(User)
        .where(
            # NOTE: User.id == id works too, but TS will complain that type is bool
            # this is only typecheck problem in query(...).where()
            col(User.id) == id
        )
        .delete()
    )
    session.commit()
    return {"delete_count": delete_count}


class TagsQuery(BaseModel):
    # http://localhost:8000/_dev/test-get/doge?tags=foo&tags=bat&category_ids=1&category_ids=2'
    tags: list[str]
    category_ids: list[int]


@router.get("/test-get/{path}", responses={200: {"model": datetime.datetime}})
def dev_test_get(
    *,
    path: str,
    # pydantic model as query can't be combined with regular
    # page: int = 0,
    # page_size: int = 20,
    # show_hidden: bool = False,
    # after: datetime.datetime | None = None,
    filter: Annotated[TagsQuery, Query()],
):
    return {
        "path": path,
        "filter": filter,
        # "page": page,
        # "page_size": page_size,
        # "show_hidden": show_hidden,
        # "after": after or datetime.datetime.now(),
    }
    # return JSONResponse(jsonable_encoder(messrespon), status_code=200)


@router.post("/set-session")
def dev_set_session(request: Request, data: dict[str, str]):
    for k, v in data.items():
        if not v:
            del request.session[k]
        else:
            request.session[k] = v
    result_session = dict(request.session)
    return result_session


class DevUploadFile(BaseModel):
    file: Annotated[UploadFile, File()]
    images: Annotated[list[UploadFile], File()]
    name: str


@router.post("/upload-file")
def dev_upload_file(
    form: Annotated[DevUploadFile, Form(media_type="multipart/form-data")],
    # file: Annotated[UploadFile, File()],
    # images: Annotated[list[UploadFile], File()],
    # name: Annotated[str, Form()],
):
    file = form.file
    images = form.images
    name = form.name

    file_dir = os.path.join(UPLOAD_DIR, "dev-file")
    images_dir = os.path.join(UPLOAD_DIR, "dev-images")
    os.makedirs(file_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)

    save_file(file, file_dir)
    for image in images:
        save_file(image, images_dir)

    # ext = mimetypes.guess_extension(file.content_type)
    # with open(
    #     os.path.join(file_dir, f"upload-{name}-{uuid.uuid4()}.{ext}"),
    #     "wb",
    # ) as fdst:
    #     shutil.copy(file, fdst)

    # for file in images:
    #     shutil.copy(
    #         file.file.name,
    #         os.path.join(
    #             images_dir,
    #             f"upload-{name}-{uuid.uuid4()}.{file.filename.split('.')[-1]}",
    #         ),
    #     )

    # print("type", file.content_type)
    # print("filename", file.filename)

    return {
        "message": {
            "file": {
                "type": file.content_type,
                "filename": file.filename,
                "size": file.size,
            },
            "images": [
                {
                    "type": file.content_type,
                    "filename": file.filename,
                    "size": file.size,
                }
                for file in images
            ],
            "name": name,
        }
    }
