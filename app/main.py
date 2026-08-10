"""FastAPI application factory for the Todo App.

A single process serves HTML routes and (from 1.2+) mutations (AD-2). The schema
is created on startup via a lifespan handler — no separate migration step in v1
(the spine defers Alembic). Using a lifespan (not the deprecated
``@app.on_event``) means TestClient's context-manager entry initialises the DB.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import db as dbmod
from app.routes.health import router as health_router
from app.routes.todos import router as todos_router

_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    dbmod.init_db()
    try:
        yield
    finally:
        if dbmod.engine is not None:
            dbmod.engine.dispose()  # release connections on shutdown


def create_app() -> FastAPI:
    app = FastAPI(title="Todo App", lifespan=lifespan)
    app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")
    app.include_router(health_router)
    app.include_router(todos_router)
    return app


app = create_app()
