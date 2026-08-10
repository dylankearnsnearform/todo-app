"""E2E — Story 1.2 client-side validation display (AC#2 / AD-5).

Locks the behavior that was previously only hand-verified: an empty submit shows
the gentle validation message in #add-error (via the htmx:beforeSwap handler), and
a subsequent valid submit appends the item and clears the error.
"""

from __future__ import annotations

import pytest
from playwright.sync_api import expect


@pytest.mark.e2e
def test_validation_message_shown_then_cleared(page, base_url: str, network_monitor) -> None:  # noqa: ANN001
    network_monitor.allow_status(422)  # the empty submit intentionally returns 422
    page.goto(base_url)

    # Empty submit → gentle message routed into #add-error
    page.get_by_role("button", name="Add").click()
    expect(page.locator("#add-error")).to_contain_text("Please enter a description.")

    # Valid submit → item appended and the error is cleared
    page.get_by_role("textbox").fill("Real task")
    page.get_by_role("button", name="Add").click()
    expect(page.locator("#todo-list")).to_contain_text("Real task")
    expect(page.locator("#add-error")).to_have_text("")

    network_monitor.assert_clean()
