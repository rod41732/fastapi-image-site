import logging
from fastapi import FastAPI
import os
import sys

from fastapi.staticfiles import StaticFiles

# important stuff
cwd = os.path.dirname(__file__)
sys.path.append(cwd)


from starlette.middleware.sessions import SessionMiddleware
from routes import user, dev, artworks


app = FastAPI()

session_secret = "very-secret-string"
app.add_middleware(SessionMiddleware, secret_key=session_secret)
app.include_router(user.router, prefix="/user", tags=["user"])
app.include_router(dev.router, prefix="/_dev", tags=["dev"])
app.include_router(artworks.router, prefix="/artworks", tags=["artworks"])
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# @app.on_event("startup")
# def on_server_start():
#     logging.info("Executing 'startup' events")
#     create_db_and_tables()
