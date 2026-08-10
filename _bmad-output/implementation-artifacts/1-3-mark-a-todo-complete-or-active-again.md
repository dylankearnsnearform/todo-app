---
baseline_commit: NO_VCS
---

# Story 1.3: Mark a todo complete or active again

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want to toggle a task between done and not-done,
so that I can track progress and correct mistakes.

## Acceptance Criteria

1. **Toggle flips + persists + swaps in place.** Given an active Todo in the list, when I toggle it (HTMX request to a toggle route), then its `completed` status flips and is **persisted (committed)**, and its **item fragment is swapped in place instantly** (FR-5) — a completed Todo rendered **visually distinct** from an active one. *(FR-3, AD-4, AD-7; risk R2)*
2. **Reversible / idempotent per target state.** Given a completed Todo, when I toggle it again, then it returns to active and persists. The write is deterministic per resulting state (setting the same state twice yields the same state). *(FR-3)*
3. **Persisted status reflected on reload.** Given a toggled Todo, when I reload the page, then the persisted status is shown. *(FR-3, FR-9)*
4. **Toggling a nonexistent id is handled (not a 500).** Given a stale tab / already-removed Todo, when I toggle an id that does not exist, then the server returns a proper **404 + rendered error fragment** (AD-5), no unhandled 500, and no row is changed. *(risk R3; AD-5)*

## Tasks / Subtasks

- [x] **Task 1 — Toggle route** (AC: #1, #2, #4)
  - [x] Add `POST /todos/{todo_id}/toggle` to `app/routes/todos.py`.
  - [x] Load the Todo by id via `get_session()`. **Missing → return `_error.html` with status 404** (AD-5/R3); do not touch any row.
  - [x] Present → flip `completed`, **`session.commit()` explicitly**, `session.refresh`, return the `_todo_item.html` fragment reflecting the new state (AD-4/AD-7).
  - [x] Match the established style: SQLAlchemy 2.0 (`session.get(Todo, id)` or `select`), thin route (route → DB write → HTML fragment), templates never touch the DB.
- [x] **Task 2 — Toggle control in the item template** (AC: #1)
  - [x] Add a toggle control to `app/templates/_todo_item.html` (reused by list render, create response, and now toggle): a checkbox (`checked` when `todo.completed`) with `hx-post="/todos/{{ todo.id }}/toggle"`, `hx-target="#todo-{{ todo.id }}"`, `hx-swap="outerHTML"` so the item **replaces itself** with the new-state fragment.
  - [x] The completed styling already exists (`.completed` in `app.css` + the `completed` class on the item root). Ensure the swapped fragment keeps the stable root id `todo-<id>` (AD-7) so repeat toggles keep working.
- [x] **Task 3 — Tests (ATDD red → green)** (AC: #1–#4)
  - [x] **Recommended:** run `bmad-testarch-atdd` first for the 1.3 red scaffolds, then drive them green.
  - [x] Implement the designed scenarios [test-design-epic-1.md]: **1.3-INT-001** (active→completed persists + completed marker in fragment), **1.3-INT-002** (completed→active, reversible), **1.3-INT-003** (toggle nonexistent id → 404 + error fragment, no 500).
  - [x] The existing `tests/integration/test_example_api.py::test_toggle_missing_todo_returns_error_fragment` must still pass — now it exercises the real route (must return 404, not 500).
  - [x] Reuse harness helpers: `TodoClient.toggle(id)` (already posts to `/todos/{id}/toggle`), `assert_single_item_fragment` (AD-7), `session_for`/`insert_todo` to seed, the `client` fixture.
  - [x] `make test` green. Optional E2E: extend the UJ-1 journey (add → toggle styles done) — the full add→toggle→delete E2E (`1.X-E2E-001`) completes in Story 1.4.

### Review Findings

_Code review 2026-07-17 (adversarial: Blind Hunter + Edge Case Hunter + Acceptance Auditor). 5 patch, 2 deferred, 3 dismissed. All 4 ACs met at the server contract level; findings are test-coverage + a11y + polish._

- [x] [Review][Patch] [med] AC3 (reflected on reload) has no automated coverage — tests assert persistence via direct DB reads only; add an integration test: toggle → `GET /` → rendered fragment shows `checked`/`completed`. [tests/integration/test_story_1_3_toggle.py]
- [x] [Review][Patch] [med] AC4 "no row is changed" under-proven — the bad-id test runs against an empty DB (asserts count 0); seed a real todo and assert it is untouched when toggling a different (missing) id. [tests/integration/test_story_1_3_toggle.py:71]
- [x] [Review][Patch] [low] a11y: `outerHTML` self-replacement drops keyboard/SR focus — give the checkbox a stable `id="toggle-{{ todo.id }}"` so htmx restores focus to it after the swap. [app/templates/_todo_item.html:2]
- [x] [Review][Patch] [low] Redundant `session.refresh(todo)` in toggle — with `expire_on_commit=False` the flipped value + id are already live; drop the extra SELECT (unlike `create`, which needs it for the generated PK). [app/routes/todos.py:80]
- [x] [Review][Patch] [low] Misleading "idempotent" label — the toggle is a reversible *flip*, not idempotent-per-target; fix the test docstring/comment wording (spine's "idempotent per target state" nuance noted as deferred). [tests/integration/test_story_1_3_toggle.py:11]
- [x] [Review][Defer] [med] Toggle/mutation error is not surfaced in the browser — htmx ignores non-2xx swaps and the 1.2 `beforeSwap` handler is scoped to `#add-form`, so a toggle 404 is fetched and discarded (checkbox left visually flipped in a stale tab). [app/routes/todos.py:72, app/templates/index.html] — deferred, mutation-error UI display is Epic 2 (FR-7/AD-5), as the story states. **AD-7 hazard for Epic 2:** the error fragment must target a separate region, NOT replace the item via `#todo-{id}` outerHTML (that would destroy the row).
- [x] [Review][Defer] [low] Lost update on concurrent/rapid toggles — unguarded read-modify-write flip (no row lock/version); two interleaved toggles net one flip [app/routes/todos.py:78] — deferred, personal-scale single-user in v1; revisit with multi-user/auth (AD-6).

## Dev Notes

### Building on Stories 1.1 + 1.2 (reuse — do NOT reinvent) 🚨

Stories 1.1 and 1.2 are `done`. Toggle is a small, well-trodden addition. **Extend, don't recreate** [Source: 1-1…md, 1-2-add-a-new-todo.md]:

| Already exists | Use it for 1.3 |
| --- | --- |
| `app/routes/todos.py` — `GET /`, `POST /todos` (2.0 `select()`, explicit commit, `get_session()`) | add `POST /todos/{id}/toggle` in the same style |
| `app/models.py` — `Todo` (`completed` boolean) | flip `Todo.completed` |
| `app/templates/_todo_item.html` — single root `<li id="todo-{{id}}" class="todo-item{% if completed %} completed{% endif %}">` | add the toggle control here (reused everywhere) |
| `app/templates/_error.html` — error fragment (wired for 422 in 1.2) | reuse for the **404** path (AD-5/R3) |
| `app/static/app.css` — `.completed` (strikethrough/dimmed) | already styles completed items; no change needed |
| `app/db.py` — WAL + busy_timeout, `get_session()` | reuse as-is |
| `tests/support/clients.py::TodoClient.toggle(id)` | reuse in tests |
| `tests/support/db.py` (`session_for`, `insert_todo`) + `fragments.assert_single_item_fragment` | seed + assert |

### Swap mechanics (important difference from 1.2)

- 1.2 **appended** a new item to `#todo-list` (`hx-swap="beforeend"`). 1.3 **replaces an existing item in place**: the toggle control targets its own item (`hx-target="#todo-{{ todo.id }}"`, `hx-swap="outerHTML"`), and the route returns the same item fragment with the flipped state. The stable root id `todo-<id>` (AD-7) makes the self-replacement idempotent across repeated toggles (risk R2).
- Because `_todo_item.html` is the single item template, adding the toggle control there makes create responses and list renders carry it too — intended (one source of truth, no fragment drift).

### Error path (AD-5 / R3) — the new bit

- Toggling a **nonexistent id** (stale tab, already-deleted) must return **404 + a rendered error fragment**, never an unhandled 500 (`session.get(Todo, id)` → `None` → 404 + `_error.html`).
- **Scope note:** the inline `htmx:beforeSwap` handler added in 1.2 is scoped to `#add-form`, so it will NOT hijack a toggle 404 — correct. Surfacing mutation errors *in the UI* (non-disruptive display for toggle/delete failures) is broader AD-5/FR-7 work owned by **Epic 2**; 1.3 only needs the correct server response (status + fragment), which the integration test asserts.

### Architecture guardrails (binding)

[Source: ARCHITECTURE-SPINE.md]

- **AD-4** route → DB write → HTML fragment; **explicit commit**; templates never touch the DB.
- **AD-5** failed request → proper HTTP status **and** rendered error fragment (AC #4).
- **AD-7** item fragment is a single root element `todo-<id>`; the toggle swap targets/returns exactly that.
- **Convention:** `completed` boolean; toggling deterministic per resulting state.

### Version-specific patterns

- Prefer `session.get(Todo, todo_id)` (SQLAlchemy 2.0) for the primary-key lookup.
- HTMX checkbox: the default trigger for a checkbox is `change`, so `hx-post` fires on toggle without extra config. Keep the control accessible (a real `<input type="checkbox">` with an `aria-label`).

### Scope boundaries (resist creep)

- **In scope:** toggle complete↔active (+ its 404 path). Nothing else.
- **Out of scope:** delete (1.4); responsive/empty/loading/error-UX polish (Epic 2); the full add→toggle→delete E2E journey (completes in 1.4). Editing text is a v1 non-goal. [Source: prd.md §5]

### ATDD Artifacts

Red-phase scaffolds generated and skipped — **activate one per task** (remove `@pytest.mark.skip`), confirm RED, implement to GREEN.

- Checklist: `_bmad-output/test-artifacts/atdd-checklist-1-3-mark-a-todo-complete-or-active-again.md`
- New scaffolds: `tests/integration/test_story_1_3_toggle.py` (1.3-INT-001/002/003) — RED-verified against the current app (no toggle route).
- Regression: `tests/integration/test_example_api.py::test_toggle_missing_todo_returns_error_fragment` now hits the real route (must stay ≤404, not 500).

Contract pinned: `POST /todos/{id}/toggle` → present: flip `completed` + commit + return `_todo_item.html` (single-root `todo-<id>`, completed marker reflects new state); missing: **404 + `_error.html`**.

### Project Structure Notes

Extends existing files only: `app/routes/todos.py` (+toggle route), `app/templates/_todo_item.html` (+toggle control). New tests in `tests/integration/test_story_1_3_toggle.py`. No new files/deps. No conflicts.

### Testing

- **Framework:** pytest + `TestClient` (integration) / pytest-playwright (e2e). `make test` / `make test-e2e`. [Source: tests/README.md]
- **Designed coverage (this story)** [Source: test-design-epic-1.md]:
  - `1.3-INT-001` — active→completed persists + completed marker in fragment (R2; FR-3/AD-7)
  - `1.3-INT-002` — completed→active, reversible/idempotent per target (FR-3)
  - `1.3-INT-003` — toggle nonexistent id → 404 + error fragment, no 500 (R3; AD-5)
  - Regression: `test_example_api.py::test_toggle_missing_todo_returns_error_fragment` now hits the real route.
- **Discipline:** deterministic, isolated; seed via `session_for`/`insert_todo`; assert fragment shape + `completed` marker; assert 404 (not 500) for the bad-id path.
- **Done gate:** the three 1.3 scenarios green + the toggle example api test green + full `make test` green.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-1.3]
- [Source: _bmad-output/planning-artifacts/prds/prd-nearform_python-2026-07-14/prd.md] (FR-3 toggle; §9 assumption: completion is a reversible toggle)
- [Source: _bmad-output/planning-artifacts/architecture/architecture-nearform_python-2026-07-14/ARCHITECTURE-SPINE.md] (AD-4, AD-5, AD-7; completion convention)
- [Source: _bmad-output/test-artifacts/test-design/test-design-epic-1.md] (1.3 scenarios; risks R2/R3)
- [Source: _bmad-output/implementation-artifacts/1-2-add-a-new-todo.md] (create-route patterns, scoped beforeSwap handler, reuse map)
- [Source: tests/README.md] (harness helpers, run commands)

## Dev Agent Record

### Agent Model Used

claude-opus-4-8 (BMad dev-story workflow)

### Debug Log References

- RED: activated 3 scaffolds → 3 failures (no toggle route → 404; bad-id test rejected FastAPI's default `{"detail":"Not Found"}`).
- GREEN: after toggle route + checkbox control → all 3 pass; toggle example-api regression (`tests/api/test_example_api.py`) 2 passed.
- Live browser: active → check → completed (in-place `outerHTML` swap) → reload persists (checkbox checked) → uncheck → active.
- Full suite: 25 passed, 2 skipped (e2e excluded), + `make test-e2e` 2 passed.

### Completion Notes List

- All 4 ACs satisfied; verified by 1.3-INT-001/002/003 + the toggle example-api test + a live browser toggle/reload cycle.
- **In-place swap** (differs from 1.2's append): checkbox in `_todo_item.html` uses `hx-target="#todo-{id}"` + `hx-swap="outerHTML"`; the route returns the same fragment with flipped state; stable `todo-<id>` root keeps repeat toggles working (AD-7).
- **404 path (AD-5/R3):** missing id → `session.get` None → 404 + `_error.html` (no 500). The 1.2 `beforeSwap` handler is scoped to `#add-form`, so it correctly does not hijack this 404 (UI display of mutation errors remains Epic 2).
- Reused everything: `TodoClient.toggle`, `_todo_item.html`/`_error.html`, `session_for`/`insert_todo`, `get_session`, WAL. No new files/deps.
- Note: the toggle example-api test lives at `tests/api/test_example_api.py` (story text said `integration/`); it passes at the real path.

### File List

**Modified (application):**
- `app/routes/todos.py` (+`POST /todos/{id}/toggle`)
- `app/templates/_todo_item.html` (+toggle checkbox control)

**New (tests, this story):**
- `tests/integration/test_story_1_3_toggle.py`

## Change Log

| Date | Change |
| --- | --- |
| 2026-07-17 | Implemented Story 1.3 (toggle complete/active): `POST /todos/{id}/toggle` (flip + commit + item fragment; missing → 404 + `_error.html`) and a checkbox control in `_todo_item.html` with in-place `outerHTML` swap. 1.3-INT-001/002/003 + toggle regression + live browser cycle green; 25 passed / 2 e2e. Status → review. |
| 2026-07-17 | Code review: applied 5 patches — added AC3 reload-render test + strengthened AC4 bad-id test (seeds a real row, asserts untouched), gave the checkbox a stable `id="toggle-{id}"` for keyboard-focus retention across the swap (verified live), removed the redundant `session.refresh` in toggle, fixed the misleading "idempotent" test wording. 2 deferred (mutation-error UI + concurrency → Epic 2 / multi-user), 3 dismissed. 26 passed + 2 e2e. Status → done. |
