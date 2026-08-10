"""Shared Jinja2 templates instance.

Kept in one place so routes render from a single, autoescaped environment
(autoescape is on for `.html` — descriptions are never marked ``| safe``,
pre-empting stored-XSS via user text).
"""

from __future__ import annotations

import os

from fastapi.templating import Jinja2Templates

_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

templates = Jinja2Templates(directory=_TEMPLATES_DIR)
