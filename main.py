# important stuff
import os
import sys

sys.path.append(os.path.dirname(__file__))

import htpy as h
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from libs.dependencies import CurrentUserOrNone
from libs.html import page_layout
from routes import artworks, dev, user

app = FastAPI()

session_secret = "very-secret-string"
app.add_middleware(SessionMiddleware, secret_key=session_secret)
app.include_router(user.router, prefix="/user", tags=["user"])
# /user/login
app.include_router(dev.router, prefix="/_dev", tags=["dev"])
app.include_router(artworks.router, prefix="/artworks", tags=["artworks"])

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=RedirectResponse)
def get_root():
    return "/index.html"


@app.get("/index.html", response_class=HTMLResponse, include_in_schema=False)
def main_page(user: CurrentUserOrNone):
    return str(
        page_layout(
            user=user,
            body=[
                h.div(style="padding: 16px 24px;")[
                    h.h1["Welcome to the site"],
                    user is None
                    and [
                        h.div[
                            "Login -> ",
                            h.a(href="/users/login.html")["Login"],
                        ],
                        h.div[
                            "Register -> ",
                            h.a(href="/users/register.html")["Register"],
                        ],
                    ],
                    h.div[
                        "Gallery -> ",
                        h.a(href="/artworks/gallery.html")["Gallery"],
                    ],
                ]
                # [
                #     h.h1["Some random content"],
                #     h.div(style="width: 200px; height: 125vh; background: blue; "),
                #     h.p[
                #         "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Maecenas ligula ipsum, ullamcorper rhoncus laoreet a, tristique sit amet leo. Vestibulum urna lorem, commodo eget faucibus at, viverra non mauris. Nam quis augue quam. Pellentesque viverra enim ut accumsan tristique. Etiam blandit pellentesque elit, a laoreet ex. Suspendisse gravida sed ipsum vitae tincidunt. Cras laoreet, felis id aliquet facilisis, urna eros suscipit urna, quis fermentum sapien mauris id ante. Cras fermentum pellentesque ullamcorper.  "
                #     ],
                # ]
                # * 10,
            ],
        )
    )


# @app.on_event("startup")
# def on_server_start():
#     logging.info("Executing 'startup' events")
#     create_db_and_tables()
