# QA Report — Todo App

Date: 2026-08-10 · Scope: Epic 1 (view / add / toggle / delete).
Method: QA integrated throughout development (test-design → ATDD red scaffolds →
implementation → adversarial code review), not bolted on at the end.

---

## 1. Test Coverage

**Target:** ≥ 70% meaningful coverage. **Result: 96%** (branch coverage enabled).

| Module | Stmts | Miss | Cover |
| --- | --- | --- | --- |
| `app/db.py` | 37 | 2 | 91% |
| `app/main.py` | 24 | 0 | 96% |
| `app/models.py` | — | 0 | 100% |
| `app/routes/todos.py` | — | 0 | 100% |
| `app/routes/health.py` | 14 | 2 | 86% |
| `app/templating.py` | — | 0 | 100% |
| **TOTAL** | **146** | **4** | **96%** |

Command: `pytest -m "not e2e" --cov=app --cov-report=term-missing`.

**Why it's meaningful (not vanity coverage):** tests assert *behavior and contracts*,
not just line execution — e.g. HTMX fragment shape (single root `todo-<id>`, AD-7),
DB row counts after mutations, 404-vs-500 on missing ids, HTML escaping of a
`<script>` payload, and durability across an engine dispose/reopen. The 4 uncovered
lines are defensive branches (a `get_session()` "not initialised" guard and the
health-check failure path) that aren't reachable in the normal test flow.

**Suite composition:**

| Level | Count | What it proves |
| --- | --- | --- |
| Unit | 3 | validation, config guard, model defaults |
| Integration (TestClient) | ~23 | routes, persistence, fragment contracts, error paths |
| E2E (Playwright) | 6 | real-browser journeys + accessibility |
| **Total** | **32 + 6 E2E** | |

**Gap analysis (AI-assisted):** code review surfaced coverage gaps the initial
generation missed — reload-render (AC3), "no full page reload" (AC4), and
"delete removes only the targeted row." All were added; see the per-story
`Review Findings` sections.

---

## 2. Accessibility

**Target:** Zero critical WCAG violations / WCAG AA. **Result: 0 violations at any
impact level; 28 axe-core rules passed.**

- Tool: **axe-core** driven from Playwright (`axe-playwright-python`), run against a
  populated page (input + list item + toggle checkbox + delete button).
- Automated in the suite: `tests/e2e/test_accessibility.py` fails on any *critical*
  violation; the standalone audit for this report found **zero** across all impacts
  (critical / serious / moderate / minor).
- Rulesets: axe defaults (WCAG 2.0/2.1 A & AA + best-practice).

**Design choices that earned this:** semantic HTML (`<main>`, `<h1>`, `<ul>/<li>`,
real `<button>`/`<input type=checkbox>`), `lang="en"`, `aria-label`s on the toggle
and delete controls, `aria-live` on the error slot, and a viewport meta tag.

**Honest caveat:** automated tooling covers roughly a third of WCAG success criteria.
A full AA claim would also need manual checks (keyboard-only walkthrough, screen-reader
pass, focus order, contrast in all states). Keyboard focus retention across HTMX swaps
*was* verified manually (the toggle checkbox keeps focus after its `outerHTML` swap).

---

## 3. Security Review

**Method:** AI-assisted static review of the application code for the common web
risk classes (XSS, injection, CSRF, validation, secrets, error leakage), plus a
pattern scan. Vendored `htmx.min.js` (v2.0.4) is treated as a trusted third-party
library and excluded from the app-code scan.

| # | Area | Finding | Severity | Status / Remediation |
| --- | --- | --- | --- | --- |
| S1 | **XSS (stored/reflected)** | User `description` is rendered through Jinja2 with **autoescape ON**; no `\| safe` anywhere. A `<script>` payload renders escaped. | — | ✅ Mitigated; asserted by test `1.2-INT-004` |
| S2 | **SQL injection** | All DB access is via SQLAlchemy 2.0 ORM (`session.get`, `select(Todo)`, `add`/`delete`). No user input is string-concatenated into SQL. Raw `text()` appears only for `SELECT 1` (health) and static `PRAGMA`s. | — | ✅ Mitigated (parameterized/ORM) |
| S3 | **Input validation** | `description` validated: non-empty after trim and ≤ 500 chars; missing/empty/oversized → `422` + error fragment, no row written. | — | ✅ Mitigated; tests `1.2-INT-003`, `1.2-UNIT-001`, over-length test |
| S4 | **Mass assignment** | Create accepts only the `description` form field; `id`, `completed`, `created_at` are server-controlled. | — | ✅ Not exploitable |
| S5 | **CSRF** | State-changing routes (`POST /todos`, `POST /todos/{id}/toggle`, `DELETE /todos/{id}`) have no CSRF token. | **Low** | Accepted for v1: no auth/session/cookies exist, so there is no ambient credential to forge; htmx is configured `selfRequestsOnly`. **Remediation when auth lands (AD-6): add CSRF tokens / SameSite cookies.** Tracked in `deferred-work.md`. |
| S6 | **Error information leakage** | Handled errors return generic messages (404/422 + friendly fragment). An unhandled 500 (e.g. commit failure) would return FastAPI's default generic 500 (no stack trace unless run in debug mode). | **Low** | Ensure the app is **not** run with `--reload`/debug in production. Graceful mutation-error UI is deferred to Epic 2. |
| S7 | **Secrets management** | No hardcoded secrets/keys/passwords; `DATABASE_URL` comes from the environment. | — | ✅ Clean |
| S8 | **In-memory DB guard** | `resolve_database_url()` refuses in-memory SQLite forms (`:memory:`, `mode=memory`, bare `sqlite://`) and non-SQLite schemes, preventing silent data loss / misconfiguration. | — | ✅ Hardened (unit-tested) |
| S9 | **Container hardening** | Image runs as a **non-root** user (`appuser`, uid 10001); SQLite volume owned by that user; multi-stage build keeps test/build tooling out of the runtime image. | — | ✅ Good posture |
| S10 | **Transport security** | The app serves plain HTTP. | Info | Terminate TLS at a reverse proxy / platform in real deployment (out of v1 scope). |

**Summary:** no High or Critical findings. The two Low items (CSRF, 500 handling)
are both tied to capabilities intentionally out of v1 scope (auth, rich error UX) and
are tracked for the epics that introduce them.

---

## 4. Performance

**Target (NFR-2):** interactions feel instantaneous — visible result well under a
second. **Result: met with large margin** at the server layer.

| Endpoint | Server response time (local) |
| --- | --- |
| `GET /` (list render) | ~3.5 ms |
| `GET /health` | ~1.8 ms |
| `POST /todos` (create + commit) | ~1.6 ms |

Method: `curl` total-time against the containerized app with a seeded DB.

**Honest tooling note:** the assignment suggests **Chrome DevTools MCP** for
performance profiling; that MCP was **not used** (see §6). The measurements above
are server-side latency only (not a full front-end profile of paint/interaction
timings). For a personal-scale hypermedia app with server-rendered fragments and no
client bundle, server latency is the dominant factor, and it is ~2–4 ms — orders of
magnitude under the NFR. Front-end profiling (Lighthouse/DevTools) is a reasonable
follow-up but was not required to meet NFR-2.

---

## 5. Test Infrastructure

- **Runner:** pytest (unit/integration/api) + pytest-playwright (E2E) — one command, shared fixtures.
- **Isolation:** each test gets a throwaway file-backed SQLite DB (a real file, so durability is genuinely exercised).
- **E2E:** self-managed live uvicorn server per session; a network-error monitor fails tests on unexpected 4xx/5xx.
- **CI:** `.github/workflows/test.yml` (fast job + browser E2E job).
- **In-container tests:** `docker compose run --rm test` (verified: 32 passed on Python 3.12).

---

## 6. Tooling Used vs. Assignment Template (transparency)

The assignment template assumes a frontend+backend+DB split and several **MCP
servers**. This project is a single hypermedia monolith with embedded SQLite, and
**no MCP servers were used**. What was done instead:

| Template suggestion | What we actually used |
| --- | --- |
| Postman MCP for API contracts | FastAPI `TestClient` integration tests assert routes + fragment contracts |
| Chrome DevTools MCP for perf/debug | `curl` latency + live Playwright browser instrumentation for debugging |
| Playwright **MCP** for E2E | Playwright **library** (`pytest-playwright`) — same engine, driven from the test suite |

This is documented honestly in `AI-INTEGRATION-LOG.md` §2.
