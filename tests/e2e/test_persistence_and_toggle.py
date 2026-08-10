"""E2E — browser-level persistence and toggle styling (FR-9 / FR-3).

Complements the integration suite by proving these behaviors through a real
browser + live server, not just TestClient.
"""

from __future__ import annotations

import re

import pytest
from playwright.sync_api import expect


@pytest.mark.e2e
def test_added_todo_persists_after_reload(page, base_url: str, network_monitor) -> None:  # noqa: ANN001
    """FR-9: a todo added in the browser is still there after a full reload."""
    page.goto(base_url)
    page.get_by_role("textbox").fill("Persist across reload")
    page.get_by_role("button", name="Add").click()
    expect(page.locator("#todo-list")).to_contain_text("Persist across reload")

    page.reload()

    expect(page.locator("#todo-list")).to_contain_text("Persist across reload")
    network_monitor.assert_clean()


@pytest.mark.e2e
def test_toggle_marks_completed_in_browser(page, base_url: str, network_monitor) -> None:  # noqa: ANN001
    """FR-3: toggling in the browser applies the completed styling in place."""
    page.goto(base_url)
    page.get_by_role("textbox").fill("Toggle in browser")
    page.get_by_role("button", name="Add").click()
    item = page.locator("#todo-list li", has_text="Toggle in browser")
    expect(item).to_have_count(1)

    item.get_by_role("checkbox").check()

    expect(item).to_have_class(re.compile(r"completed"))
    network_monitor.assert_clean()
