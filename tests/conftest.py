"""Root test configuration and shared fixtures.

Design notes
------------
This is a *greenfield* harness: the FastAPI app (``app.main:app``, ``app.db``,
``app.models``) does not exist yet. Every fixture that touches the app therefore
imports it lazily via ``pytest.importorskip`` so the suite runs green (as skips)
today and lights up automatically the moment the app is created.

Assumptions the app should honour (documented in tests/README.md):
  * FastAPI instance is exposed as ``app.main:app``.
  * The database URL is read from the ``DATABASE_URL`` environment variable.
    The suite points this at a throwaway temp SQLite file per run so tests never
    touch dev data (satisfies risk R1 — durability tests own a real file DB).
  * Using ``TestClient`` as a context manager triggers the app's startup event,
    which is expected to create the schema (spine defers migrations; v1 creates
    the schema on startup).
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest

# Make the `tests.support` helpers importable as `support.*` too, and keep the
# project root on the path so `import app...` resolves once the app exists.
pytest_plugins: list[str] = []


# ---------------------------------------------------------------------------
# Collection: keep the default `pytest` run fast by excluding e2e unless asked.
# ---------------------------------------------------------------------------
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Deselect e2e tests unless the run explicitly targets them.

    Runs `pytest` -> unit + integration + api (fast, no browser).
    Runs `pytest -m e2e` (or `make test-e2e`) -> only the browser tests.
    """
    marker_expr = config.getoption("-m", default="") or ""
    if "e2e" in marker_expr:
        return  # user explicitly asked for e2e — respect it
    skip_e2e = pytest.mark.skip(reason="e2e excluded from default run; use `pytest -m e2e`")
    for item in items:
        if "e2e" in item.keywords:
            item.add_marker(skip_e2e)


# ---------------------------------------------------------------------------
# Database isolation
# ---------------------------------------------------------------------------
@pytest.fixture
def test_db_path(tmp_path: Path) -> Path:
    """A unique, throwaway SQLite file path for a single test (parallel-safe)."""
    return tmp_path / "test_todo.db"


@pytest.fixture
def test_db_url(test_db_path: Path) -> str:
    """SQLAlchemy URL for the throwaway DB. Deliberately a *file*, not :memory:,
    so restart-durability tests (R1) exercise real persistence."""
    return f"sqlite:///{test_db_path}"


@pytest.fixture
def app_env(monkeypatch: pytest.MonkeyPatch, test_db_url: str) -> None:
    """Point the app at the throwaway DB before it is imported/started."""
    monkeypatch.setenv("DATABASE_URL", test_db_url)
    monkeypatch.setenv("TEST_ENV", os.getenv("TEST_ENV", "local"))


# ---------------------------------------------------------------------------
# In-process app client (integration + api tests)
# ---------------------------------------------------------------------------
@pytest.fixture
def app_module(app_env: None):
    """The imported FastAPI application module.

    Skips cleanly with a clear message until the app is built.
    """
    return pytest.importorskip(
        "app.main",
        reason="app.main not found yet — build the FastAPI app to enable these tests "
        "(see tests/README.md 'App contract').",
    )


@pytest.fixture
def client(app_module) -> Iterator["object"]:
    """FastAPI TestClient bound to a fresh throwaway DB.

    Used as a context manager so the app's startup/shutdown events fire — the app
    is expected to create its schema on startup.
    """
    from fastapi.testclient import TestClient  # local import: only needed here

    with TestClient(app_module.app) as test_client:
        yield test_client
