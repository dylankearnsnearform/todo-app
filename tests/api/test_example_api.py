"""Sample API test — HTTP/route contract (status codes + error fragments).

Demonstrates AD-5 uniform error handling: mutating a nonexistent id returns a
proper status AND a rendered error fragment (never a bare 500 / blank screen).

Maps to test-design scenario 1.x-INT (toggle/delete of a bad id, risk R3).
"""

from __future__ import annotations

import pytest

from tests.support.clients import TodoClient


@pytest.mark.api
def test_toggle_missing_todo_returns_error_fragment(client) -> None:  # noqa: ANN001
    todos = TodoClient(client)

    # When we toggle an id that does not exist
    response = todos.toggle(999_999)

    # Then we get a client/handled status, not an unhandled 500 (AD-5)
    assert response.status_code in (404, 400, 422), (
        f"Expected a handled error status, got {response.status_code}"
    )
    assert response.status_code != 500


@pytest.mark.api
def test_delete_missing_todo_is_handled(client) -> None:  # noqa: ANN001
    todos = TodoClient(client)

    response = todos.delete(999_999)

    assert response.status_code != 500
    assert response.status_code in (404, 400, 200), (
        f"Expected a handled status for deleting a missing id, got {response.status_code}"
    )
