"""Sample E2E test — full browser via Playwright against a live server.

Deliberately minimal: the test-design keeps E2E to ~2 happy-path scenarios and
pushes most coverage down to integration. This one verifies the HTMX swap works
end-to-end in a real browser (the thing integration tests can't prove).

Demonstrates: Playwright auto-waiting (no hard sleeps), the network-error monitor,
and a role/text selector strategy (prefer accessible selectors; fall back to
data-testid on the app side).

Maps to test-design scenario 1.x-E2E-001 (create-and-see-it happy path).
"""

from __future__ import annotations

import pytest


@pytest.mark.e2e
def test_create_todo_shows_in_list(page, base_url: str, network_monitor) -> None:  # noqa: ANN001
    # Given the app's index page
    page.goto(base_url)

    # When the user adds a todo (form submit triggers an HTMX swap)
    description = "Walk the dog"
    page.get_by_role("textbox").first.fill(description)
    page.get_by_role("button", name="Add").click()

    # Then the new item appears in the list container (auto-waited, no sleeps)
    todo_list = page.locator("#todo-list")
    expect_visible = todo_list.get_by_text(description)
    expect_visible.wait_for(state="visible")

    # And no unexpected network errors occurred during the swap (AD-5 confidence)
    network_monitor.assert_clean()
