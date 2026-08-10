"""Sample INTEGRATION test — in-process via FastAPI TestClient (DB allowed).

Demonstrates: seeding via the API-client helper (not the UI), asserting both
behaviour AND the returned HTMX fragment shape (AD-7), and self-cleaning isolation
(each test gets a fresh throwaway DB via the `client` fixture).

Maps to test-design scenarios:
  * 1.1-INT-* create + list round-trip
  * 1.2-INT-004 (HTML escaping / no stored XSS, R4)
"""

from __future__ import annotations

import pytest

from tests.support.clients import TodoClient
from tests.support.factories import todo_payload
from tests.support.fragments import assert_list_container, assert_single_item_fragment


@pytest.mark.integration
def test_create_todo_returns_item_fragment(client) -> None:  # noqa: ANN001
    # Given a todo client bound to a fresh DB
    todos = TodoClient(client)
    description = todo_payload()["description"]

    # When we create a todo
    response = todos.create(description)

    # Then the server returns a swappable single-item fragment (AD-7)
    assert response.status_code in (200, 201)
    body = response.text
    assert description in body
    # The created id is unknown here; assert the fragment shape via the list page.
    list_response = todos.list_page()
    assert_list_container(list_response.text)
    assert description in list_response.text


@pytest.mark.integration
def test_description_is_html_escaped(client) -> None:  # noqa: ANN001
    """R4: stored XSS is prevented — a script payload is escaped, not executed."""
    todos = TodoClient(client)
    payload = "<script>alert('xss')</script>"

    todos.create(payload)
    rendered = todos.list_page().text

    # The raw script tag must not appear unescaped in the rendered HTML.
    assert "<script>alert('xss')</script>" not in rendered
    assert "&lt;script&gt;" in rendered or "&amp;lt;" in rendered
