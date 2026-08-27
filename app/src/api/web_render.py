"""Shared template rendering for the server-rendered web interface (feature 005).

Renders full pages and bare fragments from a single Jinja2 environment. Templates
live in ``app/src/templates``. Autoescaping is on so candidate-derived content
(pros/cons, evidence) renders as inert text (spec FR-009).
"""
from __future__ import annotations

import os

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

_TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
_STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")

templates = Jinja2Templates(directory=_TEMPLATES_DIR)


def templates_dir() -> str:
    return _TEMPLATES_DIR


def static_dir() -> str:
    return _STATIC_DIR


def render_page(request: Request, name: str, context: dict, status_code: int = 200) -> HTMLResponse:
    """Render a full page template with the current user in context."""
    return templates.TemplateResponse(request, name, context, status_code=status_code)


def render_fragment(request: Request, name: str, context: dict, status_code: int = 200) -> HTMLResponse:
    """Render a bare HTML fragment (no full-page chrome) for in-place swapping."""
    return templates.TemplateResponse(request, name, context, status_code=status_code)
