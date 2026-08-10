# Test Suite — Todo App

A single **pytest** runner covers every layer. Integration tests drive the app
in-process via FastAPI `TestClient`; E2E tests drive a real browser via
**Playwright (Python)**. This matches the test-design's "test trophy" shape
(integration-heavy, ~2 E2E).

## Layout

```
tests/
  conftest.py              # shared fixtures: throwaway DB, TestClient, e2e gating
  unit/                    # fast, isolated logic (no I/O)          [marker: unit]
  integration/             # in-process via TestClient (DB allowed) [marker: integration]
  api/                     # route/status + error-fragment contract [marker: api]
  e2e/                     # browser via Playwright + live server    [marker: e2e]
    conftest.py            # live uvicorn server, base_url, network monitor
  support/
    factories.py           # data factories with overrides (Faker)
    clients.py             # TodoClient — intent-revealing route helpers
    fragments.py           # AD-7 HTMX fragment/swap assertions
    monitors.py            # network-error monitor for browser tests
```

## Setup

```bash
make install            # pip install -e ".[test]"
make install-browsers   # playwright install --with-deps chromium   (for E2E)
```

## Running

```bash
make test               # everything except E2E (fast; no browser)
make test-unit          # pytest -m unit
make test-integration   # pytest -m integration
make test-api           # pytest -m api
make test-e2e           # browser E2E (boots a live server automatically)
make test-cov           # coverage over the in-process suite
```

`pytest` on its own runs unit + integration + api. E2E is opt-in
(`pytest -m e2e`) because it launches a browser and a server.

## Greenfield behaviour

The app isn't built yet, so every app-dependent test **skips with a clear
message** until the code exists — the suite is green today and lights up
automatically as the app appears. Nothing here needs editing to "turn on."

## App contract (what the app must expose for these tests)

The fixtures assume the architecture spine's shape. When you build the app, honour:

| Assumption | Where used | Spine ref |
| --- | --- | --- |
| FastAPI instance at `app.main:app` | `client`, `live_server` fixtures | Structural seed |
| Reads DB URL from `DATABASE_URL` env var | DB isolation | "config, not hard-coded" |
| Creates schema on startup (TestClient context triggers it) | `client` fixture | migrations deferred |
| Routes verb-scoped under `/todos` (create `POST /todos`, toggle `POST /todos/{id}/toggle`, delete `DELETE /todos/{id}`) | `TodoClient` | naming convention |
| List container has stable id `todo-list`; each item root id `todo-<id>` | `fragments.py`, E2E | **AD-7** |
| Errors return a handled status + rendered error fragment (never bare 500) | `api/` tests | **AD-5** |
| `app.models.is_valid_description(str) -> bool` (optional helper) | unit sample | R5 validation |

If the app settles on different route paths, change them once in
`support/clients.py` — the tests won't need touching.

## Conventions

- **Factories over static fixtures** — `todo_payload()` / `todo_record()` accept
  overrides; Faker keeps values collision-free for parallel runs.
- **Seed via API/DB, not the UI** — the UI is for validation only.
- **No hard waits** — rely on TestClient's synchronous responses and Playwright's
  auto-waiting (`expect`/`wait_for`), never `sleep`.
- **Self-cleaning isolation** — each test gets a throwaway SQLite file; nothing
  leaks between tests.
- **Assert the fragment contract** — mutation responses are checked for the AD-7
  swap shape, not just status codes.

## CI integration

A ready-to-use workflow lives at `.github/workflows/test.yml`. It runs two jobs:

1. **fast** — `pytest -m "not e2e" --cov=app` (unit + integration + api). No browser.
2. **e2e** — installs Chromium (`playwright install --with-deps chromium`), then
   `pytest -m e2e`. The suite boots its own live server, so no separate service
   step is needed.

Notes for wiring into CI:

- Cache pip and the Playwright browser download to keep runs fast.
- The default `pytest` excludes e2e, so the fast job needs no extra flags.
- Artifacts: pass `--tracing=retain-on-failure --video=retain-on-failure` on the
  e2e job and upload `test-results/` on failure for debugging traces.
- A fuller quality pipeline (gates, sharding, reporting) can be generated later
  with the `bmad-testarch-ci` skill.

## Knowledge base references

Patterns here are ports of the TEA knowledge fragments to Python:

- **data-factories** — factory functions with overrides + Faker (`support/factories.py`)
- **test-quality** — deterministic, isolated, no hard waits, self-cleaning
- **fixture-architecture** — composable, lazily-loaded fixtures (`conftest.py`)
- **network-first / network-error-monitor** — `support/monitors.py` fails on
  unexpected 4xx/5xx during browser tests
