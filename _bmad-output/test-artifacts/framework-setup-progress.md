---
stepsCompleted: ['step-01-preflight', 'step-02-select-framework', 'step-03-scaffold-framework', 'step-04-docs-and-scripts', 'step-05-validate-and-summary']
lastStep: 'step-05-validate-and-summary'
workflowStatus: 'completed'
lastSaved: '2026-07-17'
---

# Framework Setup Progress

## Step 1 — Preflight

**Detected stack:** `fullstack` (Python backend + server-rendered hypermedia UI)

**Project:** nearform_python — Todo App (greenfield; no application code yet)

**Intended stack (from Architecture Spine):**
- Server-rendered hypermedia monolith: FastAPI + Jinja2 + HTMX + SQLite
- Python 3.12+ (venv present; no pyproject.toml yet)
- No JS build / no package.json (HTMX vendored)

**Existing test framework:** none (clean slate)

**Test intent (test-design-epic-1.md):** integration-heavy "test trophy" —
19 scenarios = 3 unit / 14 integration / 2 E2E. Integration via FastAPI
TestClient asserting HTMX fragment structure; 2 browser E2E for swap happy-path.

**Prerequisite note:** app manifest/code not yet generated (greenfield).
User elected to scaffold the **full test harness** now:
- pytest + FastAPI TestClient (unit/integration)
- Playwright for Python (pytest-playwright) for E2E
Cypress rejected — Node-only, poor fit for a pure-Python project.

## Step 2 — Framework Selection

**Detected stack:** fullstack → select browser + backend frameworks.
`config.test_framework: auto` → architect decides.

| Layer | Framework |
| --- | --- |
| Unit + Integration | pytest + FastAPI TestClient (httpx) |
| E2E (browser) | Playwright for Python (pytest-playwright) |

**Rationale:** Language match (Python); TestClient asserts behavior + HTMX
fragment structure in-process; Playwright drives a real browser for HTMX swap
verification (AD-7) with auto-waiting + trace-on-failure. Everything runs under
a single `pytest` runner sharing fixtures. Cypress rejected (Node-only).

## Step 3 — Scaffold Framework

**Execution mode:** sequential (single session).

**Playwright Utils note:** config `tea_use_playwright_utils: true` targets the
Node package `@seontechnologies/playwright-utils` — N/A for a pure-Python project.
Its principles (fixture composition, auto-cleanup, data factories, network-error
monitoring) were ported to idiomatic pytest + pytest-playwright.

**Files created:**
- `pyproject.toml` — app deps + `[test]` extra + pytest/coverage config + markers
- `.python-version` (3.12), `.env.example`, `.gitignore`, `Makefile` (test targets)
- `tests/` tree: `unit/`, `integration/`, `api/`, `e2e/`, `support/`
- `tests/conftest.py` — throwaway-DB isolation, TestClient `client` fixture,
  e2e auto-exclusion from default run, lazy `importorskip` app loading
- `tests/e2e/conftest.py` — session-scoped self-managed uvicorn `live_server`,
  `base_url` override, `browser_context_args`, `network_monitor`
- `tests/support/` — `factories.py` (Faker + overrides), `clients.py` (TodoClient),
  `fragments.py` (AD-7 swap assertions), `monitors.py` (network-error monitor)
- Sample tests per layer mapped to test-design scenarios (R3/R4/R5, AD-5, AD-7)
- `tests/README.md` — usage + the **app contract** the code must honour

**Greenfield strategy:** all app-dependent tests `importorskip` → suite is green
(skips) today, lights up automatically once `app/main.py` exists.

**VERIFICATION (ran in venv):**
- Collection clean (9 tests). Default `pytest`: 1 passed, 8 skipped (clear msgs).
- `pytest -m e2e` with no app: clean skip (no ScopeMismatch after session-scope fix).
- Proven against a throwaway FastAPI stub matching the documented contract:
  - `pytest -m "not e2e"` → **8 passed**
  - `pytest -m e2e` (chromium + live server) → **1 passed**
  Stub discarded afterward; repo left with harness only.

**Bug found & fixed during verification:** function-scoped `base_url` override
clashed with pytest-base-url's session-scoped autouse `_verify_url`
(ScopeMismatch) → made `live_server`/`base_url` session-scoped.

## Step 4 — Documentation & Scripts

- `tests/README.md` extended with **CI integration notes** and **knowledge-base
  references** (data-factories, test-quality, fixture-architecture, network-first).
- Test scripts: `Makefile` targets (`test`, `test-unit/integration/api/e2e`,
  `test-cov`, `install`, `install-browsers`) — Python idiom, no package.json.
- Added `.github/workflows/test.yml`: `fast` job (unit+integration+api + coverage)
  and `e2e` job (Chromium + self-booting live server, artifacts on failure).
- Fuller CI pipeline deferred to the `bmad-testarch-ci` skill.

## Step 5 — Validation & Summary

Validated against `checklist.md` (which is Node/TS/Playwright-JS-oriented; items
mapped to Python equivalents, genuine N/A marked):

| Checklist area | Status | Python equivalent / note |
| --- | --- | --- |
| Prerequisites: manifest exists | ✅ (now) | `pyproject.toml` created this run (was greenfield) |
| Stack detected / no conflicts | ✅ | fullstack; no prior test framework |
| Framework justified & announced | ✅ | pytest + pytest-playwright; Cypress rejected |
| Directory structure + `support/` | ✅ | `tests/{unit,integration,api,e2e,support}` |
| Framework config valid | ✅ | `[tool.pytest.ini_options]` (no playwright.config.ts — Python) |
| Timeouts / artifacts | ✅ | Playwright defaults + CLI flags in Makefile/CI |
| `.env.example` (TEST_ENV/BASE_URL/API_URL) | ✅ | present |
| Version file | ✅ | `.python-version` (no `.nvmrc` — not Node) |
| Fixtures + auto-cleanup | ✅ | throwaway-DB per test; session live server |
| Data factories + Faker | ✅ | `support/factories.py` with overrides |
| Sample tests, G/W/T, assertions | ✅ | one per layer, mapped to test-design |
| Helpers (API/network/monitor) | ✅ | `clients.py`, `fragments.py`, `monitors.py` |
| Docs: setup/run/arch/best-practice/CI/KB/troubleshoot | ✅ | `tests/README.md` |
| Test scripts | ✅ | `Makefile` (no package.json — Python) |
| No placeholders/secrets | ✅ | scanned clean |
| Sample test executes | ✅ | verified vs stub: 8 pass (non-e2e) + 1 e2e |
| Pact CDC alignment | N/A | `tea_use_pactjs_utils: false` |
| mergeTests / index.ts / TS types | N/A | Node/TS-only concepts |

**Selector-strategy note:** checklist prefers `data-testid`; the sample E2E uses
accessible role selectors (`get_by_role`) which are preferred for a hypermedia
app, with `data-testid` as documented fallback in the README.

**Downstream readiness:** compatible with `bmad-testarch-ci`, `-test-design`
(already done for Epic 1), and `-atdd`.

**Recommended follow-up:** log framework init in
`_bmad-output/implementation-artifacts/sprint-status.yaml` when convenient
(left untouched here to avoid clobbering sprint-planning's file).

**WORKFLOW COMPLETE.**
