"""ATDD red-phase scaffolds — Story 1.4 "Delete a todo" (integration level).

TDD RED PHASE: every test is `@pytest.mark.skip`. Activate ONE per task (remove
the skip), watch it fail (no `DELETE /todos/{id}` route yet), implement to green.

Reuses harness fixtures/helpers: `client`, `test_db_url`, `TodoClient.delete()`,
`tests.support.db` seeding helpers.

Scenarios (from test-design-epic-1.md):
  1.4-INT-001 [P0] delete removes row + returns removal response (empty 200)
  1.4-INT-002 [P1] deleted todo absent on reload
  1.4-INT-003 [P1] delete nonexistent id → 404 + error fragment, no 500, other rows untouched (R3/AD-5)
"""

from __future__ import annotations

import re

import pytest

from tests.support.clients import TodoClient
from tests.support.db import insert_todo, session_for

_ITEM_ID = re.compile(r'id=["\']todo-(\d+)["\']')


def _todo_count(db_url: str) -> int:
    from sqlalchemy import func, select

    from app.models import Todo

    with session_for(db_url) as (session, _engine):
        return session.scalar(select(func.count()).select_from(Todo)) or 0


@pytest.mark.integration
def test_delete_removes_row_and_returns_removal_response(client, test_db_url: str) -> None:  # noqa: ANN001
    """FR-4/AD-4: delete removes the row and returns an empty body so the
    outerHTML swap drops the element."""
    with session_for(test_db_url) as (session, _engine):
        todo_id = insert_todo(session, description="delete me").id

    response = TodoClient(client).delete(todo_id)

    assert response.status_code == 200
    assert response.text.strip() == ""  # empty removal response
    assert _todo_count(test_db_url) == 0


@pytest.mark.integration
def test_delete_removes_only_the_targeted_row(client, test_db_url: str) -> None:  # noqa: ANN001
    """FR-4: deleting one todo leaves the others intact."""
    from app.models import Todo

    with session_for(test_db_url) as (session, _engine):
        keep_id = insert_todo(session, description="keep me").id
        drop_id = insert_todo(session, description="drop me").id

    response = TodoClient(client).delete(drop_id)

    assert response.status_code == 200
    assert _todo_count(test_db_url) == 1
    with session_for(test_db_url) as (session, _engine):
        assert session.get(Todo, keep_id) is not None
        assert session.get(Todo, drop_id) is None


@pytest.mark.integration
def test_delete_twice_second_is_404(client, test_db_url: str) -> None:  # noqa: ANN001
    """Stale-tab idempotency: re-deleting an already-removed id returns 404, not 500."""
    todos = TodoClient(client)
    with session_for(test_db_url) as (session, _engine):
        todo_id = insert_todo(session, description="once").id

    first = todos.delete(todo_id)
    second = todos.delete(todo_id)

    assert first.status_code == 200
    assert second.status_code == 404
    assert 'role="alert"' in second.text or "alert" in second.text.lower()
    assert _todo_count(test_db_url) == 0


@pytest.mark.integration
def test_deleted_todo_absent_on_reload(client, test_db_url: str) -> None:  # noqa: ANN001
    """FR-4: a deleted todo does not reappear on reload."""
    todos = TodoClient(client)
    with session_for(test_db_url) as (session, _engine):
        todo_id = insert_todo(session, description="gone-forever").id

    todos.delete(todo_id)

    body = todos.list_page().text
    assert "gone-forever" not in body
    assert _ITEM_ID.search(body) is None


@pytest.mark.integration
def test_delete_nonexistent_returns_404_error_fragment(client, test_db_url: str) -> None:  # noqa: ANN001
    """R3/AD-5: deleting a missing id returns 404 + rendered error fragment, not 500,
    and leaves other (real) rows untouched."""
    from app.models import Todo

    with session_for(test_db_url) as (session, _engine):
        real_id = insert_todo(session, description="real").id

    response = TodoClient(client).delete(999_999)

    assert response.status_code == 404
    assert 'role="alert"' in response.text or "alert" in response.text.lower()
    assert _todo_count(test_db_url) == 1
    with session_for(test_db_url) as (session, _engine):
        assert session.get(Todo, real_id) is not None
