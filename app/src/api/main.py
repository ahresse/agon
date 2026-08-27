"""FastAPI application entrypoint (T016)."""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from src.api import (
    auth,
    reviews_detail,
    reviews_list,
    reviews_weights,
    submissions,
    tests as tests_router,
    users,
    web,
)
from src.api.web_auth import _RedirectException
from src.api.web_render import static_dir
from src.config import settings
from src.db import init_db
from src.services.job_queue import queue
from src.tests_plugins import ai_agent_example
from src.tests_plugins import metric_example
from src.tests_plugins.quality.builtin import register_quality_plugins
from src.tests_plugins.registry import registry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agon")


def register_plugins() -> None:
    """Register built-in plugins idempotently (quality suite + AI-agent)."""
    register_quality_plugins(registry)
    if ai_agent_example.KEY not in registry.keys():
        registry.register(ai_agent_example.KEY, ai_agent_example.factory)
    # Legacy example metric kept registered for backward-compatible seeds/tests.
    if metric_example.KEY not in registry.keys():
        registry.register(metric_example.KEY, metric_example.factory)


def create_app() -> FastAPI:
    app = FastAPI(title="Agon Code Review API", version="0.1.0")
    register_plugins()
    # JSON API routers.
    app.include_router(auth.router)
    app.include_router(submissions.router)
    app.include_router(reviews_list.router)
    app.include_router(reviews_detail.router)
    app.include_router(reviews_weights.router)
    app.include_router(tests_router.router)
    app.include_router(users.router)
    # Server-rendered web interface (feature 005) + static assets.
    app.mount("/static", StaticFiles(directory=static_dir()), name="static")
    app.include_router(web.router)

    @app.exception_handler(_RedirectException)
    async def _handle_redirect(request: Request, exc: _RedirectException) -> RedirectResponse:
        return exc.response

    @app.on_event("startup")
    def _startup() -> None:
        init_db()
        if not settings.run_jobs_inline:
            queue.start()
        logger.info("Agon backend started; plugins=%s", registry.keys())

    @app.on_event("shutdown")
    def _shutdown() -> None:
        queue.stop()

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
