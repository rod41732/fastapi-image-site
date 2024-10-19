from fastapi.responses import HTMLResponse, RedirectResponse
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
                src="https://unpkg.com/htmx.org@2.0.3",
                integrity="sha384-0895/pl2MU10Hqc6jd4RvrthNlDiE9U1tWmX7WRESftEDRosgxNsQG/Ze9YMRzHq",
                crossorigin="anonymous",
            ),
            h.script(src="https://unpkg.com/htmx-ext-json-enc@2.0.1/json-enc.js"),
        ],
        h.body[
            h.div(style="display: flex; flex-direction: column; height: 100vh;")[
                h.div(
                    style="padding: 8px 16px; flex: 0 0 auto; background: #fafafa; display: flex; align-items: center; column-gap: 16px"
                )[
                    h.h1["FastAPI Image site"],
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
                            h.form(method="POST", action="/user/logout.html")[
                                h.button(type="submit")["Logout"]
                            ],
                        ]
                    ),
                ],
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
