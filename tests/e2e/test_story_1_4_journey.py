"""E2E — the full UJ-1 journey (test-design 1.X-E2E-001).

TDD RED PHASE scaffold (`@pytest.mark.skip`). Activate when Story 1.4's delete
control exists. Drives open → add → toggle → delete entirely via HTMX swaps, with
no full-page reload, asserting each step reflects instantly.
"""

from __future__ import annotations

import re

import pytest
from playwright.sync_api import expect


@pytest.mark.e2e
def test_open_add_toggle_delete_journey(page, base_url: str, network_monitor) -> None:  # noqa: ANN001
    page.goto(base_url)
    # No-reload sentinel: a full-page navigation would wipe this window flag.
    page.evaluate("window.__noReload = true")

    # Add
    page.get_by_role("textbox").fill("Journey task")
    page.get_by_role("button", name="Add").click()
    item = page.locator("#todo-list li", has_text="Journey task")
    expect(item).to_have_count(1)  # exactly one matching row (robust locator)
    expect(item).to_be_visible()

    # Toggle → completed styling
    item.get_by_role("checkbox").check()
    expect(item).to_have_class(re.compile(r"completed"))

    # Delete → item removed from the list
    item.get_by_role("button", name=re.compile("Delete")).click()
    expect(page.locator("#todo-list")).not_to_contain_text("Journey task")

    # No unexpected network errors, and no full-page reload happened (all HTMX swaps).
    network_monitor.assert_clean()
    assert page.evaluate("window.__noReload") is True, "a full-page reload occurred during the journey"
