"""Database engine, session, and schema management (SQLAlchemy 2.0 + SQLite).

The backend is the sole writer and SQLite is the single source of truth (AD-3).
The DB URL comes from the environment, never a scattered literal (spine
convention), and an in-memory database is refused for the real store so todos
cannot silently vanish across a restart (risk R1 / FR-9).
"""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# Anchored to the project root (parent of the app package) so the SAME file is
# used regardless of the process working directory. A relative "./todo.db" would
# resolve against the launch CWD, so starting the server from another directory
# would silently open a different/empty database — an R1 durability footgun.
_DEFAULT_DB_FILE = Path(__file__).resolve().parent.parent / "todo.db"
DEFAULT_DATABASE_URL = f"sqlite:///{_DEFAULT_DB_FILE}"


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def resolve_database_url() -> str:
    """Return the SQLite URL for the real store.

    Reads ``DATABASE_URL`` (falling back to a durable file URL) and refuses any
    in-memory SQLite form — an in-memory DB would lose every todo on restart,
    violating FR-9. Tests that legitimately want an in-memory engine build one
    directly rather than routing through this guard.
    """
    # An unset OR whitespace-only DATABASE_URL means "use the default".
    url = (os.getenv("DATABASE_URL") or "").strip() or DEFAULT_DATABASE_URL
    lowered = url.lower()
    if not lowered.startswith("sqlite:"):
        raise ValueError(
            f"Only SQLite is supported for the Todo store (AD-3); got {url!r}."
        )
    # Reject every in-memory form: bare ``sqlite://``, ``:memory:`` (any case),
    # and the URI variant ``mode=memory``. An in-memory store loses all todos on
    # restart — the exact R1/FR-9 failure this guard exists to prevent.
    if url == "sqlite://" or ":memory:" in lowered or "mode=memory" in lowered:
        raise ValueError(
            f"Refusing an in-memory database for the real store: {url!r}. "
            "Set DATABASE_URL to a file-backed SQLite URL (e.g. sqlite:///./todo.db)."
        )
    return url


# Module-level handles, (re)bound by init_db(). Engine creation is deferred to
# startup so a test's DATABASE_URL override takes effect before we connect.
engine: Engine | None = None
SessionLocal: sessionmaker[Session] | None = None


def init_db() -> None:
    """Create the engine/session against the current DATABASE_URL and ensure the
    schema exists. Called from the app's lifespan handler on startup."""
    global engine, SessionLocal
    if engine is not None:
        engine.dispose()  # release the previous engine's pooled connections
    engine = create_engine(
        resolve_database_url(),
        connect_args={"check_same_thread": False},  # SQLite + threaded server
    )
    event.listen(engine, "connect", _set_sqlite_pragma)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    # Import models so their tables are registered on Base before create_all.
    from app import models  # noqa: F401  (side-effect import)

    Base.metadata.create_all(engine)


def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
    """Per-connection SQLite pragmas. WAL improves read/write concurrency and
    ``busy_timeout`` waits (instead of erroring) when the file is briefly locked —
    relevant now that mutation routes write (Story 1.2+)."""
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
    finally:
        cursor.close()


def get_session() -> Session:
    """Return a new session. Raises if the DB has not been initialised."""
    if SessionLocal is None:
        raise RuntimeError("Database not initialised — call init_db() first.")
    return SessionLocal()
