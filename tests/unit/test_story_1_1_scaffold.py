"""Story 1.1 acceptance tests (unit level).

Started as ATDD red-phase scaffolds; now activated and green against the
implementation.

Scenarios (from test-design-epic-1.md):
  1.1-UNIT-001 [P0] config guard rejects `:memory:`; default is a file URL (R1)
  1.1-UNIT-002 [P1] Todo defaults: completed=False, created_at tz-aware UTC
"""

from __future__ import annotations

import pytest


@pytest.mark.unit
def test_config_guard_rejects_in_memory_db(monkeypatch: pytest.MonkeyPatch) -> None:
    """R1 mitigation: the real DB path must never silently be in-memory.

    Contract: `app.db.resolve_database_url()` reads DATABASE_URL, falls back to a
    file URL, and raises ValueError if the resolved URL is an in-memory SQLite.
    """
    from app.db import resolve_database_url

    # In-memory forms are rejected for the real store (would lose data → FR-9 fail).
    for bad in ("sqlite:///:memory:", "sqlite://"):
        monkeypatch.setenv("DATABASE_URL", bad)
        with pytest.raises(ValueError):
            resolve_database_url()


@pytest.mark.unit
def test_default_database_url_is_a_file(monkeypatch: pytest.MonkeyPatch) -> None:
    """With DATABASE_URL unset, the app defaults to a durable file URL (not memory)."""
    from app.db import resolve_database_url

    monkeypatch.delenv("DATABASE_URL", raising=False)
    url = resolve_database_url()
    assert url.startswith("sqlite:///")
    assert ":memory:" not in url


@pytest.mark.unit
def test_todo_defaults() -> None:
    """New Todo persists with completed=False and a fresh UTC created_at.

    Note: SQLite does not preserve tz-awareness, so `created_at` reads back naive.
    The spine requires it *stored as UTC*, which we verify by value proximity to
    the current UTC time rather than by an unreliable `tzinfo` check.
    """
    from datetime import datetime, timezone

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.db import Base
    from app.models import Todo

    # Isolated in-memory engine is fine for a pure model-defaults unit test
    # (the :memory: guard governs the app's real config path, not test engines).
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        todo = Todo(description="write the model")
        session.add(todo)
        session.commit()
        session.refresh(todo)

        assert todo.completed is False
        assert todo.created_at is not None
        # created_at is a fresh UTC timestamp (compare naive-to-naive UTC).
        now_utc_naive = datetime.now(timezone.utc).replace(tzinfo=None)
        stored = todo.created_at.replace(tzinfo=None) if todo.created_at.tzinfo else todo.created_at
        assert abs((now_utc_naive - stored).total_seconds()) < 120
