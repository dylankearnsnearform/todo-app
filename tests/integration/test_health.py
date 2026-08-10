"""Health endpoint tests (container readiness/liveness)."""

from __future__ import annotations

import pytest


@pytest.mark.integration
def test_health_ok(client) -> None:  # noqa: ANN001
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
