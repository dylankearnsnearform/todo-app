"""API-first helpers for driving the app through its routes.

These wrap the FastAPI TestClient so integration/api tests read as intent
("create a todo", "toggle it") rather than raw HTTP plumbing. Route paths follow
the architecture spine (verb-scoped under ``/todos``); adjust here in one place if
the app settles on different paths — tests stay unchanged.
"""

from __future__ import annotations

from typing import Any


class TodoClient:
    """Thin, intent-revealing wrapper over a FastAPI TestClient.

    Every method returns the raw ``httpx.Response`` so tests can assert on both
    status code and the returned HTML fragment (the hypermedia contract, AD-7).
    """

    def __init__(self, client: Any, base: str = "/todos") -> None:
        self._client = client
        self._base = base

    def list_page(self) -> Any:
        """GET the full page (index) that renders the todo list."""
        return self._client.get("/")

    def create(self, description: str) -> Any:
        """POST a new todo (form-encoded, as HTMX submits it)."""
        return self._client.post(self._base, data={"description": description})

    def toggle(self, todo_id: int) -> Any:
        """POST toggle completion for a todo id."""
        return self._client.post(f"{self._base}/{todo_id}/toggle")

    def delete(self, todo_id: int) -> Any:
        """DELETE a todo by id."""
        return self._client.delete(f"{self._base}/{todo_id}")
