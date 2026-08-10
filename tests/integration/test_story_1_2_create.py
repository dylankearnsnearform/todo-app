"""ATDD red-phase scaffolds — Story 1.2 "Add a new todo" (integration level).

TDD RED PHASE: every test is `@pytest.mark.skip`. Activate ONE per task (remove
the skip), watch it fail (no `POST /todos` route yet → 404), then implement to green.

Reuses harness fixtures/helpers: `client` (throwaway file DB), `test_db_url`,
`TodoClient.create()` (posts form-encoded to `/todos`), `assert_single_item_fragment`
(AD-7), and `tests.support.db` seeding helpers.

Scenarios (from test-design-epic-1.md):
  1.2-INT-001 [P0] create → persists (active, ts) + returns single-root `todo-<id>` fragment (R2)
  1.2-INT-002 [P1] created todo present on reload (R1)
  1.2-INT-003 [P1] empty/whitespace POST → 422, validation fragment, NO new row (R5)
  1.2-INT-004 [P1] `<script>` description HTML-escaped in the returned fragment (R4)

Note: 1.2-UNIT-001 (is_valid_description rejects empty/whitespace) is already green via
tests/unit/test_example_unit.py::test_description_validation — not duplicated here.
The E2E create-and-see swap is tests/e2e/test_example_e2e.py (activate in dev-story).
"""

from __future__ import annotations

import re

import pytest

from tests.support.clients import TodoClient
from tests.support.db import session_for
from tests.support.fragments import assert_single_item_fragment

_ITEM_ID = re.compile(r'id=["\']todo-(\d+)["\']')


def _todo_count(db_url: str) -> int:
    from sqlalchemy import func, select

    from app.models import Todo

    with session_for(db_url) as (session, _engine):
        return session.scalar(select(func.count()).select_from(Todo)) or 0


@pytest.mark.integration
def test_create_persists_and_returns_item_fragment(client, test_db_url: str) -> None:  # noqa: ANN001
    """FR-1/FR-8/AD-7: create persists an active todo and returns a swappable fragment."""
    todos = TodoClient(client)

    response = todos.create("Buy milk")

    assert response.status_code in (200, 201)
    match = _ITEM_ID.search(response.text)
    assert match, "create response must contain a todo-<id> element (AD-7)"
    # Returned fragment is a single root <li id="todo-N"> (append-safe swap, R2/AD-7)
    assert_single_item_fragment(response.text, int(match.group(1)))
    assert "Buy milk" in response.text

    # Persisted as active with a created_at timestamp
    from app.models import Todo

    with session_for(test_db_url) as (session, _engine):
        todo = session.get(Todo, int(match.group(1)))
        assert todo is not None
        assert todo.completed is False
        assert todo.created_at is not None


@pytest.mark.integration
def test_created_todo_present_on_reload(client) -> None:  # noqa: ANN001
    """FR-1/AD-3: a created todo is still there when the page is reloaded."""
    todos = TodoClient(client)
    todos.create("Persisted task")

    body = todos.list_page().text  # "reload" — fresh render of server state
    assert "Persisted task" in body


@pytest.mark.integration
def test_empty_description_rejected_with_message(client, test_db_url: str) -> None:  # noqa: ANN001
    """FR-1/AD-5/R5: whitespace-only input creates nothing and shows a message."""
    todos = TodoClient(client)

    response = todos.create("   ")

    # AD-5: proper error status + rendered error fragment (not a bare 500, not a silent 200)
    assert response.status_code == 422
    assert response.text.strip(), "expected a rendered validation fragment"
    assert 'role="alert"' in response.text or "alert" in response.text.lower()

    # No row created, list still empty
    assert _todo_count(test_db_url) == 0
    assert _ITEM_ID.search(todos.list_page().text) is None


@pytest.mark.integration
def test_missing_description_field_rejected(client, test_db_url: str) -> None:  # noqa: ANN001
    """R5/AD-5: the browser omits an empty input, so `description` arrives MISSING —
    it must still be handled by our validation (422 + error fragment), not a raw
    FastAPI 422 JSON. Guards the Form("") default."""
    response = client.post("/todos")  # no form data at all

    assert response.status_code == 422
    assert 'role="alert"' in response.text or "alert" in response.text.lower()
    assert "Please enter a description." in response.text
    assert _todo_count(test_db_url) == 0


@pytest.mark.integration
def test_description_is_html_escaped_in_fragment(client) -> None:  # noqa: ANN001
    """SEC/R4: a script payload is escaped in the returned fragment, never executed."""
    todos = TodoClient(client)

    response = todos.create("<script>alert('xss')</script>")

    assert response.status_code in (200, 201)
    assert "<script>alert('xss')</script>" not in response.text
    assert "&lt;script&gt;" in response.text


@pytest.mark.integration
def test_over_length_description_rejected(client, test_db_url: str) -> None:  # noqa: ANN001
    """R5 'oversized': a description beyond the 500-char cap is rejected, no row."""
    response = TodoClient(client).create("x" * 501)

    assert response.status_code == 422
    assert "500 characters or fewer" in response.text
    assert _todo_count(test_db_url) == 0


@pytest.mark.integration
def test_max_length_description_accepted(client) -> None:  # noqa: ANN001
    """Boundary: exactly 500 chars is accepted."""
    response = TodoClient(client).create("y" * 500)

    assert response.status_code in (200, 201)
    assert ("y" * 500) in response.text
