"""Network-error monitoring for browser (E2E) tests.

Ports the "network error monitor" idea to Playwright-Python: attach to a page and
fail the test if any request comes back 4xx/5xx that the test didn't explicitly
expect. Catches broken HTMX swaps and silent server errors that a happy-path
assertion would otherwise miss (supports AD-5 error-path confidence).
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field


@dataclass
class NetworkErrorMonitor:
    """Collects failed HTTP responses seen by a page."""

    errors: list[str] = field(default_factory=list)
    _allowed: set[int] = field(default_factory=set)

    def allow_status(self, *statuses: int) -> "NetworkErrorMonitor":
        """Whitelist expected error statuses (e.g. a deliberate 404 test)."""
        self._allowed.update(statuses)
        return self

    def _on_response(self, response) -> None:  # noqa: ANN001 - Playwright Response
        status = response.status
        if status >= 400 and status not in self._allowed:
            self.errors.append(f"{status} {response.request.method} {response.url}")

    def assert_clean(self) -> None:
        assert not self.errors, "Unexpected network errors:\n  " + "\n  ".join(self.errors)


def attach_network_monitor(page) -> Iterator[NetworkErrorMonitor]:  # noqa: ANN001
    """Context-manager-style helper: attach, yield, detach.

    Used by the ``network_monitor`` fixture in tests/e2e/conftest.py.
    """
    monitor = NetworkErrorMonitor()
    page.on("response", monitor._on_response)
    try:
        yield monitor
    finally:
        page.remove_listener("response", monitor._on_response)
