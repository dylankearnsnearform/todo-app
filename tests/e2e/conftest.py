"""E2E-only fixtures: a live server and Playwright wiring.

For ``TEST_ENV=local`` (default) the suite boots a real uvicorn server against a
throwaway SQLite DB on a random free port, and Playwright drives it. Set
``BASE_URL`` (and ``TEST_ENV=remote``) to instead point the browser at an
already-running deployment.

The ``live_server``/``base_url`` chain is **session-scoped**: the server boots
once per E2E session (fast), and this matches pytest-base-url's session-scoped
``base_url`` fixture (a function-scoped override would ScopeMismatch its autouse
``_verify_url``).

These tests require the app to exist and the Playwright browsers to be installed
(``make install-browsers``). Until then they skip cleanly.
"""

from __future__ import annotations

import os
import socket
import threading
import time
from collections.abc import Iterator

import pytest

from tests.support.monitors import NetworkErrorMonitor, attach_network_monitor


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_until_up(host: str, port: int, timeout: float = 10.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex((host, port)) == 0:
                return
        time.sleep(0.05)
    raise TimeoutError(f"Live server did not start on {host}:{port} within {timeout}s")


@pytest.fixture(scope="session")
def live_server(tmp_path_factory: pytest.TempPathFactory) -> Iterator[str]:
    """Boot the app with uvicorn in a background thread; yield its base URL.

    Skips if the app or uvicorn is unavailable. Uses a throwaway DB so E2E runs
    never touch dev data. Session-scoped: one server for the whole E2E run.
    """
    import uvicorn  # noqa: PLC0415 - optional, only needed for live E2E

    db_path = tmp_path_factory.mktemp("e2e") / "e2e_todo.db"
    previous_db_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    try:
        app_main = pytest.importorskip(
            "app.main",
            reason="app.main not found yet — build the FastAPI app to enable E2E tests.",
        )

        host, port = "127.0.0.1", _free_port()
        config = uvicorn.Config(app_main.app, host=host, port=port, log_level="warning")
        server = uvicorn.Server(config)
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        try:
            _wait_until_up(host, port)
            yield f"http://{host}:{port}"
        finally:
            server.should_exit = True
            thread.join(timeout=10)
    finally:
        if previous_db_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous_db_url


@pytest.fixture(scope="session")
def base_url(request: pytest.FixtureRequest) -> str:
    """Override pytest-base-url's fixture (must stay session-scoped).

    Prefer an explicit BASE_URL (remote target); otherwise use the self-managed
    live server. Requesting ``live_server`` lazily means remote runs never boot one.
    """
    explicit = os.getenv("BASE_URL")
    if explicit:
        return explicit
    return request.getfixturevalue("live_server")


@pytest.fixture
def browser_context_args(browser_context_args: dict) -> dict:
    """Sensible defaults for hypermedia app testing (function-scoped, per plugin)."""
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 800},
        "ignore_https_errors": True,
    }


@pytest.fixture
def network_monitor(page) -> Iterator[NetworkErrorMonitor]:  # noqa: ANN001 - Playwright Page
    """Fail the test on any unexpected 4xx/5xx. Whitelist with ``.allow_status(...)``."""
    yield from attach_network_monitor(page)
