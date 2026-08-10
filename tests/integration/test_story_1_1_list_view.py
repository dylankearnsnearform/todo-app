"""Story 1.1 acceptance tests (integration level, FastAPI TestClient).

Started as ATDD red-phase scaffolds; now activated and green against the
implementation.

Reuses harness fixtures/helpers: `client` (throwaway file DB), `test_db_url`,
`TodoClient`, `assert_list_container`, and `tests.support.db` seeding helpers.

Scenarios (from test-design-epic-1.md):
  1.1-INT-001 [P0] GET / → 200 + #todo-list container, no login, empty boundary
  1.1-INT-002 [P1] list newest-first; active + completed both shown
  1.1-INT-003 [P0] durability: written → writer disposed → still present (R1 GATE)
  1.1-INT-004 [P2] extensibility smoke: owner column addable later (AD-6)
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

import pytest

from tests.support.clients import TodoClient
from tests.support.db import insert_todo, session_for
from tests.support.fragments import assert_list_container

_ITEM_ID = re.compile(r'id=["\']todo-\d+["\']')


@pytest.mark.integration
def test_index_serves_list_container_without_login(client) -> None:  # noqa: ANN001
    """FR-2 / AD-7: `/` returns the page with a stable `#todo-list`, no auth wall."""
    response = TodoClient(client).list_page()

    assert response.status_code == 200  # not 401/redirect — no login/onboarding
    assert_list_container(response.text)  # #todo-list present (AD-7)
    # Empty-store boundary: container renders with zero item elements
    assert _ITEM_ID.search(response.text) is None


@pytest.mark.integration
def test_list_is_newest_first_and_shows_active_and_completed(client, test_db_url: str) -> None:  # noqa: ANN001
    """FR-2: newest-first ordering; both active and completed todos are shown."""
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    with session_for(test_db_url) as (session, _engine):
        insert_todo(session, description="oldest-task", created_at=base)
        insert_todo(session, description="middle-task", created_at=base + timedelta(minutes=1), completed=True)
        insert_todo(session, description="newest-task", created_at=base + timedelta(minutes=2))

    body = TodoClient(client).list_page().text

    # Newest-first
    assert body.index("newest-task") < body.index("middle-task") < body.index("oldest-task")
    # Completed item (middle) is shown alongside active ones
    assert "middle-task" in body


@pytest.mark.integration
def test_todos_survive_writer_restart(client, test_db_url: str) -> None:  # noqa: ANN001
    """FR-9 / R1: todos written then the engine disposed and reopened against the
    same file are still served.

    This is the story's done-gate — must be GREEN before 1.1 is 'done'.
    """
    from app import db as dbmod

    # Write via a separate engine, then dispose it (the writing process stops).
    with session_for(test_db_url) as (session, _engine):
        insert_todo(session, description="survives-restart")

    # Restart the app's OWN persistence: dispose + reopen the engine on the same
    # file (init_db disposes the previous engine and rebinds against DATABASE_URL).
    dbmod.init_db()

    # The reopened app still serves the persisted todo.
    response = TodoClient(client).list_page()
    assert response.status_code == 200
    assert "survives-restart" in response.text


@pytest.mark.integration
def test_owner_relationship_addable_later(test_db_url: str) -> None:
    """AD-6 / R6: no hard single-user assumption — a nullable owner column can be
    added later without restructuring, and multiple ownerless rows coexist."""
    from sqlalchemy import text

    from app.models import Todo

    with session_for(test_db_url) as (session, _engine):
        insert_todo(session, description="a")
        insert_todo(session, description="b")  # >1 row: no single-user/global-singleton constraint

        table = Todo.__tablename__
        session.execute(text(f'ALTER TABLE "{table}" ADD COLUMN owner_id INTEGER NULL'))
        session.commit()

        rows = session.execute(text(f'SELECT owner_id FROM "{table}"')).fetchall()
        assert len(rows) == 2
        assert all(row[0] is None for row in rows)  # existing rows tolerate the new nullable column
