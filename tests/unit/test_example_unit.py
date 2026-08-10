"""Sample UNIT test — fast, isolated, no I/O.

Demonstrates: Given/When/Then structure, parametrize, factory usage.
Maps to test-design scenario 1.2-UNIT-001 (description validation).

These import the app's domain layer lazily so the file collects even before the
app exists. Replace the placeholder logic with real domain calls once
``app.models`` / a validator exists.
"""

from __future__ import annotations

import pytest

from tests.support.factories import todo_payload


@pytest.mark.unit
@pytest.mark.parametrize(
    ("raw", "expected_valid"),
    [
        ("Buy milk", True),
        ("   ", False),  # whitespace-only -> rejected (R5)
        ("", False),  # empty -> rejected (R5)
    ],
)
def test_description_validation(raw: str, expected_valid: bool) -> None:
    # Given a validator from the domain layer (skips until the app defines one)
    validators = pytest.importorskip(
        "app.models",
        reason="app.models not found yet — implement Todo validation to enable.",
    )
    is_valid = getattr(validators, "is_valid_description", None)
    if is_valid is None:
        pytest.skip("app.models.is_valid_description not implemented yet")

    # When / Then
    assert is_valid(raw) is expected_valid


@pytest.mark.unit
def test_factory_produces_overridable_payload() -> None:
    # Given/When: an explicit override
    payload = todo_payload(description="Explicit intent")

    # Then: the override wins and only client-owned fields are present
    assert payload["description"] == "Explicit intent"
    assert set(payload) == {"description"}
