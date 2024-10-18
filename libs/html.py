from markupsafe import Markup
import htpy as h


_css = """
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
CSS_RESET = h.style[Markup(_css)]
