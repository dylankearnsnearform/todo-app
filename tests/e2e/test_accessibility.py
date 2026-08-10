"""E2E accessibility scan — zero critical WCAG violations (axe-core).

Loads the app with a real todo in the DOM (so the list, toggle checkbox, and
delete button are all scanned) and runs axe-core. Fails on any *critical*
violation; surfaces *serious* ones for visibility without failing (per the
success criterion "zero critical WCAG violations").
"""

from __future__ import annotations

import pytest
from axe_playwright_python.sync_playwright import Axe


@pytest.mark.e2e
def test_no_critical_wcag_violations(page, base_url: str) -> None:  # noqa: ANN001
    page.goto(base_url)
    # Populate a realistic DOM (input + item + checkbox + delete button).
    page.get_by_role("textbox").fill("Accessible task")
    page.get_by_role("button", name="Add").click()
    page.locator("#todo-list li").first.wait_for(state="visible")

    results = Axe().run(page)
    violations = results.response.get("violations", [])
    critical = [v for v in violations if v.get("impact") == "critical"]
    serious = [v for v in violations if v.get("impact") == "serious"]

    if serious:  # not a hard failure, but recorded in test output
        print("Serious (non-critical) a11y findings:", [v["id"] for v in serious])

    assert not critical, "Critical WCAG violations: " + ", ".join(
        f"{v['id']} ({len(v.get('nodes', []))} nodes)" for v in critical
    )
