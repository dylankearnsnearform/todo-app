"""Direct-persistence helpers for tests that need to seed the DB without going
through routes that don't exist yet (create/toggle/delete arrive in stories
1.2–1.4). Imports the app lazily so this module binds only once the app exists.

Seeds against the same `DATABASE_URL`/`test_db_url` the harness `client` fixture
uses, so seeded rows are visible to the running app (SQLite file, multiple
connections).
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any


@contextmanager
def session_for(db_url: str):
    """Yield ``(session, engine)`` bound to ``db_url``; ensures schema exists and
    disposes the engine on exit (simulating a writer process that stops)."""
    from sqlalchemy import create_engine  # local import: only when activated
    from sqlalchemy.orm import sessionmaker

    from app.db import Base  # noqa: PLC0415 - lazy: app may not exist yet (red phase)

    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session, engine
    finally:
        session.close()
        engine.dispose()


def insert_todo(session: Any, **overrides: Any):
    """Insert one Todo with sensible defaults; overrides win. Commits + refreshes."""
    from app.models import Todo  # noqa: PLC0415 - lazy (red phase)

    fields: dict[str, Any] = {"description": "seed"}
    fields.update(overrides)
    todo = Todo(**fields)
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo
