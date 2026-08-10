"""Health check endpoint for container orchestration.

This is an operational endpoint (not a user-facing hypermedia interaction), so it
returns JSON — the shape orchestrators/Docker HEALTHCHECK expect. It performs a
lightweight DB round-trip so "healthy" means the app can actually reach SQLite.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app import db as dbmod

router = APIRouter()


@router.get("/health")
def health() -> JSONResponse:
    """200 {"status": "ok"} when the app + DB are reachable; 503 otherwise."""
    try:
        with dbmod.get_session() as session:
            session.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001 - any DB/init failure means unhealthy
        return JSONResponse({"status": "unhealthy"}, status_code=503)
    return JSONResponse({"status": "ok"}, status_code=200)
