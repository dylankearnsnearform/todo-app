"""Story 1.3 acceptance tests — "Mark a todo complete or active again".

Started as ATDD red-phase scaffolds; now activated and green.

Reuses harness fixtures/helpers: `client`, `test_db_url`, `TodoClient.toggle()`,
`assert_single_item_fragment` (AD-7), `tests.support.db` seeding helpers.

Scenarios (from test-design-epic-1.md):
  1.3-INT-001 [P0] toggle active→completed persists + completed marker in fragment (R2)
  1.3-INT-002 [P1] toggle completed→active (reversible flip)
  1.3-INT-003 [P1] toggle nonexistent id → 404 + error fragment, no 500, other rows untouched (R3/AD-5)
  AC3        [P1] toggled state reflected on reload (GET /)
"""

from __future__ import annotations

import pytest

from tests.support.clients import TodoClient
from tests.support.db import insert_todo, session_for
from tests.support.fragments import assert_single_item_fragment

_COMPLETED_MARKER = 'class="todo-item completed"'


def _todo_count(db_url: str) -> int:
    from sqlalchemy import func, select

    from app.models import Todo

    with session_for(db_url) as (session, _engine):
        return session.scalar(select(func.count()).select_from(Todo)) or 0


@pytest.mark.integration
def test_toggle_active_to_completed(client, test_db_url: str) -> None:  # noqa: ANN001
    """FR-3/AD-7: toggling an active todo flips it to completed, persisted, and
    returns the item fragment showing the completed marker."""
    from app.models import Todo

    with session_for(test_db_url) as (session, _engine):
        todo_id = insert_todo(session, description="task", completed=False).id

    response = TodoClient(client).toggle(todo_id)

    assert response.status_code in (200, 201)
    assert_single_item_fragment(response.text, todo_id)
    assert _COMPLETED_MARKER in response.text  # visually-distinct completed marker
    with session_for(test_db_url) as (session, _engine):
        assert session.get(Todo, todo_id).completed is True


@pytest.mark.integration
def test_toggle_completed_to_active_is_reversible(client, test_db_url: str) -> None:  # noqa: ANN001
    """FR-3: toggling a completed todo returns it to active and persists."""
    from app.models import Todo

    with session_for(test_db_url) as (session, _engine):
        todo_id = insert_todo(session, description="task", completed=True).id

    response = TodoClient(client).toggle(todo_id)

    assert response.status_code in (200, 201)
    assert _COMPLETED_MARKER not in response.text  # back to active
    with session_for(test_db_url) as (session, _engine):
        assert session.get(Todo, todo_id).completed is False


@pytest.mark.integration
def test_toggle_nonexistent_returns_404_error_fragment(client, test_db_url: str) -> None:  # noqa: ANN001
    """R3/AD-5: toggling a missing id returns 404 + a rendered error fragment, not 500,
    and leaves other (real) rows untouched."""
    from app.models import Todo

    # Seed a real, unrelated todo so we can prove "no row is changed".
    with session_for(test_db_url) as (session, _engine):
        real_id = insert_todo(session, description="real", completed=False).id

    response = TodoClient(client).toggle(999_999)

    assert response.status_code == 404
    assert 'role="alert"' in response.text or "alert" in response.text.lower()
    # The real todo is untouched and still present.
    assert _todo_count(test_db_url) == 1
    with session_for(test_db_url) as (session, _engine):
        assert session.get(Todo, real_id).completed is False


@pytest.mark.integration
def test_toggle_reflected_on_reload(client, test_db_url: str) -> None:  # noqa: ANN001
    """AC3: after toggling, GET / renders the persisted state (item completed + checked)."""
    with session_for(test_db_url) as (session, _engine):
        todo_id = insert_todo(session, description="reload me", completed=False).id

    TodoClient(client).toggle(todo_id)

    body = TodoClient(client).list_page().text
    assert _COMPLETED_MARKER in body
    assert f'id="todo-{todo_id}"' in body
    assert "checked" in body  # the reloaded checkbox reflects completed state
