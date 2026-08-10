"""Data factories.

Factories return complete objects from sensible defaults plus explicit overrides.
Dynamic values (via Faker) prevent collisions in parallel runs; overrides make each
test's intent obvious. Prefer seeding state through these + the DB/API helpers over
driving the UI (UI is for validation, not setup).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from faker import Faker

_faker = Faker()


def todo_payload(**overrides: Any) -> dict[str, Any]:
    """A Todo as the *client would submit it* (form fields for an HTMX POST).

    Only the fields a user actually sends. Server-owned fields (id, created_at,
    completed) are intentionally absent.

        todo_payload()                          -> random description
        todo_payload(description="Buy milk")    -> explicit intent
    """
    return {"description": _faker.sentence(nb_words=4).rstrip("."), **overrides}


def todo_record(**overrides: Any) -> dict[str, Any]:
    """A *fully-formed* Todo record, as it would exist in storage.

    Handy for asserting rendered output or for direct DB seeding helpers.
    """
    return {
        "id": _faker.random_int(min=1, max=1_000_000),
        "description": _faker.sentence(nb_words=4).rstrip("."),
        "completed": False,
        "created_at": datetime.now(timezone.utc),
        **overrides,
    }


def seed_descriptions(count: int = 3) -> list[str]:
    """A list of distinct, collision-free descriptions for list/render tests."""
    return [f"{_faker.sentence(nb_words=3).rstrip('.')} #{i}" for i in range(count)]
