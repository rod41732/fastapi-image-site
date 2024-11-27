import logging
import mimetypes
import os
import re
import shutil
import time
from base64 import b64encode

from fastapi import UploadFile


class UploadError(Exception):
    pass

    # with open(, 'wb') as f:


def _random_id() -> str:
    """generate 12 char random characters"""
    return b64encode(os.urandom(9), altchars=b"-_").decode()


_non_word = re.compile(r"\W+")
_alnum = re.compile("^[a-zA-Z0-9]+$")


def _get_clean_file_name(name: str) -> str:
    parts = name.rsplit(".", maxsplit=1)
    namepart = parts[0]
    valid_ext = len(parts) >= 2 and re.match(_alnum, parts[1]) and len(parts[1]) <= 5
    if not valid_ext:
        namepart = name

    return re.sub(_non_word, "_", namepart).strip("_")


def save_file(file: UploadFile, dst_dir: str) -> str:
    """save file, ensure the file is named with timestamp and cleaned and with proper extension"""
    mime_type = file.content_type
    if not mime_type:
        raise UploadError("Missing content-type")
    ext = mimetypes.guess_extension(mime_type)
    if not ext:
        raise UploadError(f"Cannot determine extension for mimetype {mime_type}")

    ts = int(time.time())
    random_id = _random_id()
    clean_name = _get_clean_file_name(file.filename or "unnamed")

    name = f"{ts}.{clean_name}.{random_id}{ext}"
    dst_path = os.path.join(dst_dir, name)
    logging.info(f"-- copying {file.file.name} to {dst_path}")
    with open(dst_path, "wb") as fdst:
        shutil.copyfileobj(file.file, fdst)
    return dst_path
