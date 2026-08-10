---
baseline_commit: NO_VCS
---

# Story 1.2: Add a new todo

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want to type a task description and add it to my list,
so that I can capture something before I forget it.

## Acceptance Criteria

1. **Create persists + returns a swappable fragment.** Given the app is open, when I submit a non-empty description via the add form (HTMX request to a create route), then the route persists a new Todo (`completed=False`, `created_at` set) **committing the transaction**, and returns its **item fragment** — a single root element with id `todo-<id>` (AD-7) — which appears in `#todo-list` **instantly without a full-page reload** (FR-5). *(FR-1, FR-8, AD-4, AD-7; risk R2)*
2. **Empty/whitespace is rejected gracefully.** Given the add form, when I submit an empty or whitespace-only description, then **no Todo is created** (no new row), and a **gentle validation message** is shown via a proper HTTP error status + rendered error fragment (AD-5). The app stays usable. *(FR-1; risk R5)*
3. **Created todo survives reload.** Given a Todo was just created, when I reload the page, then the created Todo is still present (persisted via AD-3/AD-4). *(FR-1, FR-9)*
4. **Descriptions are HTML-escaped.** Given a description containing HTML/script (e.g. `<script>…`), when it is rendered in the item fragment and list, then it appears **escaped, never executed** (autoescape on; never `| safe`). *(SEC; risk R4)*

## Tasks / Subtasks

- [x] **Task 1 — Create route** (AC: #1, #2)
  - [x] Add `POST /todos` to `app/routes/todos.py`: accept form field `description: str = Form(...)` (python-multipart is already installed).
  - [x] Validate with the existing `app.models.is_valid_description` (already implemented in 1.1). Reject empty/whitespace.
  - [x] **Valid:** create `Todo(description=...)`, `session.add`, **`session.commit()` explicitly**, `session.refresh` to get the id; render and return `_todo_item.html` for the new todo. Status 200 (or 201).
  - [x] **Invalid:** return the rendered error fragment (`_error.html`) with a **422** status and a gentle message (AD-5). Do NOT insert a row.
  - [x] Keep the route thin: route → DB write → HTML fragment (AD-4). Templates never touch the DB.
- [x] **Task 2 — Add form + HTMX wiring** (AC: #1, #2)
  - [x] Add an add-todo form to `app/templates/index.html`: text input (name `description`) + submit button, with `hx-post="/todos"`, `hx-target="#todo-list"`, `hx-swap="beforeend"` (append the new item). Add an error slot (e.g. `<div id="add-error"></div>`).
  - [x] On success: new item appended to `#todo-list`; clear the input (e.g. `hx-on::after-request` reset, or return an `HX-Trigger`).
  - [x] On validation error (422): show the message without disrupting the list. Recommended no-extension pattern — the route sets response headers **`HX-Retarget: #add-error`** and **`HX-Reswap: innerHTML`** so the 422 error fragment lands in the error slot (HTMX does not swap non-2xx by default). Clear `#add-error` on the next successful add.
- [x] **Task 3 — Persistence hardening for writes** (AC: #1, #3)
  - [x] Writes now land, so address the concurrency item deferred from 1.1: enable SQLite **WAL** + a **busy_timeout** on connect (e.g. a `PRAGMA journal_mode=WAL; PRAGMA busy_timeout=5000` via a SQLAlchemy `connect`/`engine_connect` event in `app/db.py`). Keep it SQLite-guarded.
  - [x] Confirm every write path commits explicitly (test-design mitigation).
- [x] **Task 4 — Tests (ATDD red → green)** (AC: #1–#4)
  - [x] **Recommended:** run `bmad-testarch-atdd` first to generate the 1.2 red scaffolds, then drive them green.
  - [x] Activate the three example tests deferred from 1.1 (remove their `@pytest.mark.skip`): `tests/integration/test_example_integration.py::test_create_todo_returns_item_fragment`, `::test_description_is_html_escaped`, and `tests/e2e/test_example_e2e.py::test_create_todo_shows_in_list`.
  - [x] Implement the designed scenarios [test-design-epic-1.md]: **1.2-INT-001** (create persists active+ts, fragment single root `todo-<id>`), **1.2-INT-002** (created todo present on reload), **1.2-UNIT-001** (empty/whitespace rejected), **1.2-INT-003** (empty POST → not created + validation message + no new row), **1.2-INT-004** (`<script>` escaped in fragment).
  - [x] Reuse harness helpers: `TodoClient.create()` (already posts form-encoded to `/todos`), `assert_single_item_fragment` (AD-7), `todo_payload` factory, the `client` fixture. Do NOT duplicate fixtures.
  - [x] `make test` green (unit+integration+api) and `make test-e2e` green (the create-and-see swap is this story's E2E happy path).

### Review Findings

_Code review 2026-07-17 (adversarial: Blind Hunter + Edge Case Hunter + Acceptance Auditor). 1 decision, 3 patch, 3 deferred, 6 dismissed as noise._

- [x] [Review][Patch] [med] Enforce max description length = **500 chars** (resolves the R5 "oversized" decision; PRD open question #2) — reject over-length with the same 422 + error fragment; add `maxlength` on the input + a test. [app/models.py, app/routes/todos.py, app/templates/index.html]
- [x] [Review][Patch] [med] Global `htmx:beforeSwap` handler routes EVERY 422 to `#add-error` — latent cross-route hazard: a 422 from toggle/delete (1.3/1.4) or a raw FastAPI 422 would dump into the add-form slot. Scope it to the add-form request. [app/templates/index.html:12-17]
- [x] [Review][Patch] [med] AC#2 client-side validation display has NO automated test — the beforeSwap/#add-error mechanism was only hand-verified; add an E2E test (empty submit → message in `#add-error`). [tests/e2e/]
- [x] [Review][Patch] [low] a11y: `#add-error` slot has `role="status"` while injected `_error.html` has `role="alert"` — nested contradictory live-region roles. Drop the slot's role, keep `aria-live`. [app/templates/index.html:42, app/templates/_error.html:1]
- [x] [Review][Defer] [low] Commit/DB failure (disk full, lock past busy_timeout) → bare 500 the beforeSwap handler discards (only handles 422); user sees nothing [app/routes/todos.py:56] — deferred, general error-state UX is Epic 2 (FR-7/AD-5)
- [x] [Review][Defer] [low] No CSRF/origin protection on `POST /todos` [app/templates/index.html:25] — deferred, no auth/session in v1 (no forgeable surface); revisit when auth lands (AD-6)
- [x] [Review][Defer] [low] Double-submit creates duplicate todos (no button-disable/dedup) [app/templates/index.html:25] — deferred, duplicates are allowed in v1; minor UX polish (Epic 2)

## Dev Notes

### Building directly on Story 1.1 (reuse — do NOT reinvent) 🚨

Story 1.1 is `done`. The app scaffold, persistence, and list view already exist. **Extend, don't recreate** [Source: 1-1-see-my-todo-list-when-i-open-the-app.md]:

| Already exists (from 1.1) | Use it for 1.2 |
| --- | --- |
| `app/main.py` — FastAPI `app`, lifespan schema init, static mount, router | add nothing structural; the create route joins the existing router |
| `app/db.py` — `resolve_database_url` (hardened guard), `Base`, `init_db` (disposes old engine), `SessionLocal`, `get_session()` | use `get_session()`; add the WAL/busy_timeout connect event here |
| `app/models.py` — `Todo` (2.0 `Mapped`), **`is_valid_description(raw)`** already implemented | call `is_valid_description` for AC #2 |
| `app/routes/todos.py` — `GET /` list (uses `select()` 2.0 style) | add `POST /todos` here; match the 2.0 `select()`/session style |
| `app/templating.py` — shared autoescaped `templates` | render fragments through it |
| `app/templates/_todo_item.html` — single root `<li id="todo-{{ todo.id }}">` (AD-7) | **reuse as the create response fragment** (one item template, no drift) |
| `app/templates/_error.html` — error fragment (seeded in 1.1, **unwired**) | **wire it now** for the validation message (AD-5) |
| `app/templates/index.html` — page with `#todo-list`, HTMX 2.0.4 vendored + `<script>` included | add the add-form + error slot here |
| `tests/support/clients.py::TodoClient` — has `.create(description)` (POST form to `/todos`) | reuse in tests |
| `tests/support/fragments.py::assert_single_item_fragment(html, id)` | assert AC #1 fragment shape |

### Items deferred from the 1.1 review — now in scope

[Source: 1-1 Review Findings / deferred-work.md]

- **Wire `_error.html` + read/write error handling (AD-5).** 1.1 left `_error.html` seeded but unused. AC #2 requires it now for the validation message (proper status + rendered fragment).
- **SQLite WAL + busy_timeout.** 1.1 set `check_same_thread=False` with no concurrency mitigation because it was read-only. Writes land in 1.2 → add WAL + busy_timeout to avoid `database is locked` (Task 3).
- Still deferred (not this story): pagination (R8 monitor-only); true-UTC `created_at` TypeDecorator (SQLite limitation).

### Architecture guardrails (binding)

[Source: ARCHITECTURE-SPINE.md]

- **AD-1** Hypermedia: the add form is an HTMX request returning **HTML** (item fragment or error fragment) — no JSON, no client framework.
- **AD-4** All mutations flow route → DB write → HTML fragment; commit explicitly; templates never touch the DB.
- **AD-5** Failed request → proper HTTP status **and** rendered error fragment; UI stays usable (AC #2).
- **AD-7** Fixed swap contract: `#todo-list` container; each item a single root `todo-<id>`. The create response must conform so `hx-swap="beforeend"` appends cleanly (risk R2).
- **AD-6** Still holds — no single-user assumption introduced by the create path.
- **Conventions:** integer PK; `created_at` UTC (SQLite reads it back naive — known, documented); `completed` boolean default False.

### HTMX create pattern (concrete guidance)

- Form: `hx-post="/todos"`, `hx-target="#todo-list"`, `hx-swap="beforeend"`. Success → append item fragment; reset input.
- Validation error path (no HTMX extension needed): route returns **422** + `_error.html`, with response headers `HX-Retarget: #add-error` and `HX-Reswap: innerHTML` so the message lands in the error slot rather than being dropped (HTMX ignores non-2xx swaps by default). [FastAPI: set headers on the `HTMLResponse`/`TemplateResponse`.]
- Escaping (AC #4/R4): `_todo_item.html` already renders `{{ todo.description }}` autoescaped — do **not** add `| safe`. That alone satisfies R4; the test asserts a `<script>` payload is escaped.

### Version-specific patterns

[Source: ARCHITECTURE-SPINE.md#Stack — pins verified 2026-07-14]

- FastAPI form input: `from fastapi import Form`; `description: str = Form(...)`. `python-multipart` already in `pyproject.toml`.
- SQLAlchemy 2.0: match 1.1's style — `Mapped`/`mapped_column`, `select()`/`session.scalars()`; explicit `session.commit()` on the write.
- WAL pragma: use a `sqlalchemy.event.listens_for(engine, "connect")` hook that runs `PRAGMA journal_mode=WAL` and `PRAGMA busy_timeout=5000` (SQLite only).

### Scope boundaries (resist creep — SM-C1)

- **In scope:** create a todo (happy path + validation + escaping) and its instant HTMX append. That's it.
- **Out of scope:** toggle (1.3), delete (1.4), responsive/empty/loading UX polish (Epic 2). Editing a description is a v1 non-goal. [Source: prd.md §5]

### ATDD Artifacts

Red-phase acceptance scaffolds generated and skipped — **activate one per task** (remove `@pytest.mark.skip`), confirm RED, implement to GREEN.

- Checklist: `_bmad-output/test-artifacts/atdd-checklist-1-2-add-a-new-todo.md`
- New scaffolds: `tests/integration/test_story_1_2_create.py` (1.2-INT-001..004) — RED-verified against the current app (POST /todos 404).
- Also activate (deferred from 1.1): `tests/integration/test_example_integration.py::test_create_todo_returns_item_fragment` + `::test_description_is_html_escaped`, and `tests/e2e/test_example_e2e.py::test_create_todo_shows_in_list`.
- Already green (do not duplicate): `tests/unit/test_example_unit.py::test_description_validation` covers 1.2-UNIT-001 via `is_valid_description`.

Contract pinned: `POST /todos` (form `description`) → valid: 200/201 + `_todo_item.html` single-root `todo-<id>`, committed `completed=False`+`created_at`; invalid: **422** + `_error.html` (`role="alert"`), no row; autoescaped.

### Project Structure Notes

No new files strictly required — 1.2 extends existing ones: `app/routes/todos.py` (+`POST /todos`), `app/templates/index.html` (+add form/error slot), `app/db.py` (+WAL event), and reuses `_todo_item.html` / `_error.html`. New tests may add `tests/unit/test_story_1_2_*.py` / `tests/integration/test_story_1_2_*.py` alongside the activated example tests. No conflicts detected.

### Testing

- **Framework:** pytest + FastAPI `TestClient` (integration/api) and pytest-playwright (e2e). Run `make test` / `make test-e2e`. [Source: tests/README.md]
- **Designed coverage (this story)** [Source: test-design-epic-1.md]:
  - `1.2-INT-001` — create persists (active, ts) + fragment single root `todo-<id>` (R2; FR-1/FR-8/AD-7)
  - `1.2-INT-002` — created todo present on reload (R1; FR-1)
  - `1.2-UNIT-001` — empty/whitespace description rejected (R5; FR-1)
  - `1.2-INT-003` — empty POST → not created, validation message, no new row (R5; FR-1)
  - `1.2-INT-004` — `<script>` description HTML-escaped in the fragment (R4; SEC)
  - **E2E** — create-and-see swap happy path (the epic's E2E; activate `test_example_e2e.py::test_create_todo_shows_in_list`)
- **Discipline:** deterministic, isolated, no hard waits (Playwright auto-waiting for the swap); reuse `TodoClient`, `assert_single_item_fragment`, factories.
- **Done gate:** all designed 1.2 scenarios green + the three activated example tests green + full `make test` (+ `make test-e2e`) green.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-1.2]
- [Source: _bmad-output/planning-artifacts/prds/prd-nearform_python-2026-07-14/prd.md] (FR-1 create + validation, §9 assumption: empty descriptions rejected)
- [Source: _bmad-output/planning-artifacts/architecture/architecture-nearform_python-2026-07-14/ARCHITECTURE-SPINE.md] (AD-1, AD-4, AD-5, AD-7, conventions)
- [Source: _bmad-output/test-artifacts/test-design/test-design-epic-1.md] (1.2 scenarios; risks R2/R4/R5)
- [Source: _bmad-output/implementation-artifacts/1-1-see-my-todo-list-when-i-open-the-app.md] (established app contract, reuse map, deferred items now in scope)
- [Source: tests/README.md] (harness helpers, run commands)

## Dev Agent Record

### Agent Model Used

claude-opus-4-8 (BMad dev-story workflow)

### Debug Log References

- RED: activated 4 story scaffolds + 3 deferred example tests → 6 integration failures (no `POST /todos` → 404).
- GREEN (integration): after the create route → all create/escape/validation/reload integration tests pass.
- E2E: create-and-see swap passes (real browser, HTMX append).
- Full suite: 20 passed, 1 skipped (e2e excluded from default), 96% app coverage; `make test-e2e` → 1 passed.

### Implementation Plan

1. **Create route** (`app/routes/todos.py`): `POST /todos`, `is_valid_description` gate → invalid returns 422 + `_error.html`; valid persists (`add`/**explicit commit**/`refresh`) and returns `_todo_item.html`.
2. **Add form + HTMX** (`index.html`): form with `hx-post`/`hx-target=#todo-list`/`hx-swap=beforeend`, error slot `#add-error`, input reset + error clear on success.
3. **Write hardening** (`app/db.py`): SQLite WAL + `busy_timeout=5000` via a `connect` event.
4. **Tests**: activated scaffolds + example tests; all green.

### Completion Notes List

- All 4 ACs satisfied; verified by the designed 1.2 scenarios (INT-001..004) + activated example tests + E2E swap + live browser checks.
- **Deviated from the story's suggested HTMX error pattern (justified):** the recommended `HX-Retarget` + response-targets extension did **not** work with htmx 2.0.4 — the extension's `responseTargetPrefersRetargetHeader` made it defer to the header and skip the swap (`shouldSwap` stayed false). Replaced it with a tiny, self-contained inline `htmx:beforeSwap` handler that routes any 422 into `#add-error`, plus `HX-Reswap: innerHTML` for a clean replace. Removed the vendored `response-targets.min.js`.
- **Bug found via live verification + fixed:** the browser omits an empty text input, so `description` arrived **missing** → `Form(...)` raised FastAPI's own JSON 422 before our validation. Changed to `Form("")` so missing/empty both flow through `is_valid_description` → our friendly fragment. Added regression test `test_missing_description_field_rejected` (posts with no field).
- Descriptions autoescaped (no `| safe`) → R4 covered; whitespace trimmed on store.
- Carried the 1.1 deferred items into scope: `_error.html` now wired (AD-5); SQLite WAL/busy_timeout added.

### File List

**Modified (application):**
- `app/routes/todos.py` (+`POST /todos` create route)
- `app/templates/index.html` (+add form, `#add-error` slot, inline `htmx:beforeSwap` handler)
- `app/db.py` (+SQLite WAL/busy_timeout `connect` event)

**Modified (tests):**
- `tests/integration/test_story_1_2_create.py` (activated; +`test_missing_description_field_rejected`)
- `tests/integration/test_example_integration.py` (activated the 2 create/escape tests)
- `tests/e2e/test_example_e2e.py` (activated the create-swap test)
- `.gitignore` (+`*.db-wal`, `*.db-shm`)

**New (test scaffolds, this story):**
- `tests/integration/test_story_1_2_create.py`

**Note:** vendored `app/static/response-targets.min.js` was added then removed (superseded by the inline handler).

## Change Log

| Date | Change |
| --- | --- |
| 2026-07-17 | Implemented Story 1.2 (Add a new todo): `POST /todos` create route (validation → 422 + `_error.html`; valid → committed + item fragment), HTMX add form with inline `beforeSwap` error routing, SQLite WAL/busy_timeout. All designed scenarios + example tests + E2E green; 96% app coverage. Fixed missing-field handling (`Form("")`) found via live browser verification. Status → review. |
| 2026-07-17 | Code review: applied 4 patches — enforced 500-char max description (R5, PRD open-Q resolved: `description_error` + `maxlength` + tests), scoped the `beforeSwap` 422 handler to `#add-form` (prevents cross-route hijack in 1.3/1.4), added an E2E test for the validation-message display (AC#2 coverage), fixed nested a11y live-region role. 3 deferred (Epic 2 error UX / CSRF-with-auth / double-submit), 6 dismissed. 22 passed + 2 E2E. Status → done. |
