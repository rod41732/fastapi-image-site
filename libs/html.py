from fastapi.responses import HTMLResponse
from markupsafe import Markup
import htpy as h

from app.models import User


_css_reset = """
/* Reset for margins and paddings only, preserving all other styles */
html, body, div, span, applet, object, iframe,
p, blockquote, pre, a, abbr, acronym, address, big, cite, code,
del, dfn, em, img, ins, kbd, q, s, samp, small, strike, strong, sub, sup, tt, var,
b, u, i, center, dl, dt, dd, ol, ul, li, fieldset, form, label, legend,
table, caption, tbody, tfoot, thead, tr, th, td, article, aside, canvas, details,
embed, figure, figcaption, footer, header, hgroup, menu, nav, output, ruby, section,
summary, time, mark, audio, video {
  margin: 0;
  padding: 0;
}

*, *:before, *:after {
  box-sizing: border-box;
}

body {
    font-family: Sans-Serif;
}

/* Reset for tables */
table {
  border-collapse: collapse;
  border-spacing: 0;
}

/* Reset for lists */
ol, ul {
  list-style: none;
}

/* Ensure block-level elements take full width */
body {
  line-height: 1;
}

/* Reset for forms */
input, textarea, select, button {
  margin: 0;
}

/* Reset link decoration */
a {
  text-decoration: none;
}
"""
_css_base = """
body > .container {
    padding: 16px 32px;
} 

.artwork-comment {
    margin: 8px; 16px; background: #e1e1e1; padding: 8px;
}

.artwork-comment.htmx-swapping {
    background: lightpink;
}

.artwork.new {
    background-color: lightgreen;
}

.artwork.htmx-added {
    background-color: limegreen;
}


.artwork {
    padding: 8px;
    transition: background-color 1s ease-out;
}

.upload-artwork-form > p {
    margin: 8px 0px;
}

.upload-artwork-form > p > label {
    padding-right: 2em;
}

"""

_css = f"""
{_css_reset}

{_css_base}
"""
CSS_BASE = h.style[Markup(_css)]


def page_layout(user: User | None, *, body=None):
    return h.html[
        h.head[
            CSS_BASE,
            h.script(
                src="/static/htmx-2.0.3.js",
            ),
            h.script(src="/static/htmx-json-enc-2.0.1.js"),
        ],
        h.body[
            h.div(style="display: flex; flex-direction: column; height: 100vh;")[
                # Top bar
                h.div(
                    style="padding: 8px 16px; flex: 0 0 auto; background: #fafafa; display: flex; align-items: center; column-gap: 16px"
                )[
                    h.a(style="color: unset", href="/")[h.h1["FastAPI Image site"],],
                    h.a(style="color: unset", href="/artworks/gallery.html")[
                        "All Artworks"
                    ],
                    user
                    and h.a(style="color: unset", href="/artworks/mine.html")[
                        "My Artworks"
                    ],
                    h.div(style="flex: 1"),
                    (
                        [
                            h.p[
                                "Hello! Guest",
                                h.div[h.a(href="/user/login.html")["Login"],],
                                h.div[h.a(href="/user/register.html")["Register"],],
                            ],
                        ]
                        if not user
                        else [
                            h.p[
                                "Hello! ",
                                h.span(style="font-weight: bold")[user.username],
                            ],
                            h.form(hx_post="/user/logout.html")[
                                h.button(type="submit")["Logout"]
                            ],
                        ]
                    ),
                ],
                # container
                h.div(".container", style="flex: 1; overflow-x: auto")[body],
            ]
        ],
    ]


def make_redirect_response(url, refresh_duration: int = 2) -> HTMLResponse:
    return HTMLResponse(
        content=str(
            h.div[
                h.p["Redirecting..."],
                h.meta(http_equiv="refresh", content=f"{refresh_duration}; url={url}"),
            ]
        ),
        headers={
            "hx-redirect": url,
        },
    )
