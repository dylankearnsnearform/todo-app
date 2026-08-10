---
baseline_commit: NO_VCS
---

# Story 1.4: Delete a todo

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want to permanently remove a task,
so that I can clear out things I no longer care about.

## Acceptance Criteria

1. **Delete removes the row + the element, instantly.** Given a Todo in the list, when I delete it (HTMX request to a delete route), then it is removed from the store (**committed**) and its element is removed from `#todo-list` instantly, with no full-page reload (FR-5). *(FR-4, FR-8, AD-4)*
2. **Deleted todo does not reappear on reload.** Given a Todo was deleted, when I reload the page, then the deleted Todo is absent. *(FR-4, FR-9)*
3. **Deleting a nonexistent id is handled (not a 500).** Given a stale tab / already-removed Todo, when I delete an id that does not exist, then the server returns a proper **404 + rendered error fragment** (AD-5), no unhandled 500, and no other row is changed. *(risk R3; AD-5)*
4. **Full journey works end-to-end.** Given the app, when I open → add → toggle → delete, then each action reflects instantly without a full reload (the UJ-1 journey). *(FR-5, AD-7; risk R2 — E2E `1.X-E2E-001`)*

## Tasks / Subtasks

- [x] **Task 1 — Delete route** (AC: #1, #3)
  - [x] Add `DELETE /todos/{todo_id}` to `app/routes/todos.py`.
  - [x] Load via `session.get(Todo, id)`. **Missing → return `_error.html` with status 404** (AD-5/R3); do not touch any row.
  - [x] Present → `session.delete(todo)`, **`session.commit()` explicitly**, return an **empty `HTMLResponse` (200)** so the `outerHTML` swap removes the element (AD-4).
  - [x] Thin route (route → DB write → response); templates never touch the DB. Match the established 2.0/session style.
- [x] **Task 2 — Delete control in the item template** (AC: #1)
  - [x] Add a delete control to `app/templates/_todo_item.html` (reused everywhere): a button with `hx-delete="/todos/{{ todo.id }}"`, `hx-target="#todo-{{ todo.id }}"`, `hx-swap="outerHTML"` so the empty response removes the item's `<li>`.
  - [x] Keep it accessible (a real `<button>` with an `aria-label` including the description). No confirm dialog in v1 (a `hx-confirm` is possible Epic-2 polish — noted, out of scope here to keep the journey E2E simple).
- [x] **Task 3 — Tests (ATDD red → green)** (AC: #1–#4)
  - [x] **Recommended:** run `bmad-testarch-atdd` first for the 1.4 red scaffolds, then drive them green.
  - [x] Implement the designed scenarios [test-design-epic-1.md]: **1.4-INT-001** (delete removes row + returns removal response), **1.4-INT-002** (deleted todo absent on reload), **1.4-INT-003** (delete nonexistent id → 404 + error fragment, no 500, other rows untouched).
  - [x] The existing `tests/api/test_example_api.py::test_delete_missing_todo_is_handled` must still pass — now it exercises the real route (≤404, not 500).
  - [x] **E2E `1.X-E2E-001`** — full UJ-1 journey in a browser: open → add (appears instantly) → toggle (styles done) → delete (removed), all without a full reload. Reuse the `page`/`base_url`/`network_monitor` fixtures.
  - [x] Reuse harness helpers: `TodoClient.delete(id)` (already sends `DELETE /todos/{id}`), `session_for`/`insert_todo` to seed, `_todo_count`, the `client` fixture.
  - [x] `make test` green and `make test-e2e` green.

### Review Findings

_Code review 2026-07-17 (adversarial: Blind Hunter + Edge Case Hunter + Acceptance Auditor). 4 patch, 5 deferred, 3 dismissed. All 4 ACs met; findings are test-coverage + Epic-2-consistent deferrals._

- [x] [Review][Patch] [med] Journey E2E does not assert "no full reload" (AC4 clause) — `network_monitor.assert_clean()` only flags 4xx/5xx; a full-page GET would pass. Add a no-reload guard (set a `window` flag after load, assert it survives). [tests/e2e/test_story_1_4_journey.py]
- [x] [Review][Patch] [med] No test that delete removes ONLY the targeted row — happy-path seeds one row; seed two, delete one, assert the other survives. [tests/integration/test_story_1_4_delete.py]
- [x] [Review][Patch] [low] Add a sequential double-delete test (delete → 200; delete same id again → 404) — guards the stale-tab idempotency at the server. [tests/integration/test_story_1_4_delete.py]
- [x] [Review][Patch] [low] Journey E2E `has_text` is a substring match that could resolve to multiple rows — assert `to_have_count(1)` before acting. [tests/e2e/test_story_1_4_journey.py:24]
- [x] [Review][Defer] [med] Delete 404 not surfaced in the browser (fetched, discarded) [app/routes/todos.py:92] — deferred, mutation-error UI is Epic 2 (same as toggle/1.3); AD-7 note: error must target a dedicated region, not `#todo-{id}` outerHTML.
- [x] [Review][Defer] [med] Concurrency: toggle-after-delete re-materializes a phantom row; concurrent double-delete may raise StaleDataError → 500 [app/routes/todos.py:69-101] — deferred, personal-scale single-user in v1; revisit with multi-user/auth (folds into the 1.3 concurrency item).
- [x] [Review][Defer] [low] No confirm/undo on delete → accidental data loss [app/templates/_todo_item.html:13] — deferred, documented v1 decision; `hx-confirm`/undo is Epic-2 UX polish.
- [x] [Review][Defer] [low] No empty-state when the last todo is deleted (bare empty `<ul>`) [app/templates/index.html] — deferred, empty state is Epic 2 (FR-7, Story 2.2).
- [x] [Review][Defer] [low] Silent 500 on delete commit failure (unguarded) [app/routes/todos.py:100] — deferred, general error-state UX is Epic 2 (FR-7/AD-5); same as toggle.

## Dev Notes

### Building on Stories 1.1–1.3 (reuse — do NOT reinvent) 🚨

Delete is the smallest mutation and mirrors toggle almost exactly. **Extend, don't recreate** [Source: 1-1…, 1-2-add-a-new-todo.md, 1-3-mark-a-todo-complete-or-active-again.md]:

| Already exists | Use it for 1.4 |
| --- | --- |
| `app/routes/todos.py` — `GET /`, `POST /todos`, `POST /todos/{id}/toggle` (2.0 `session.get`, explicit commit, `get_session()`, 404 → `_error.html`) | add `DELETE /todos/{id}` in the **same shape as toggle** (the 404 path is identical) |
| `app/templates/_todo_item.html` — item root `<li id="todo-{{id}}">` + toggle checkbox (`id="toggle-{{id}}"`) | add the delete button alongside the checkbox |
| `app/templates/_error.html` — error fragment (reused for 404 in 1.3) | reuse for the delete 404 (AD-5/R3) |
| `app/db.py` — WAL + busy_timeout, `get_session()` | reuse as-is |
| `tests/support/clients.py::TodoClient.delete(id)` | reuse in tests |
| `tests/support/db.py` (`session_for`, `insert_todo`) | seed + assert row counts |
| `tests/e2e/` fixtures (`page`, `base_url`, `network_monitor`) | drive the full-journey E2E |

### Swap mechanics — removal (differs from 1.2 append / 1.3 replace)

- Delete uses `hx-target="#todo-{{ todo.id }}"` + `hx-swap="outerHTML"` and an **empty 200 body** → the item's `<li>` is replaced with nothing, i.e. removed from `#todo-list`. No fragment is rendered on success (the only mutation that returns empty).
- The 404 error path is identical to toggle's (`session.get` → None → 404 + `_error.html`); the same Epic-2 deferral applies (see below).

### Error path + the deferred mutation-error UI (carried from 1.3)

- Server contract (this story): delete-missing → **404 + `_error.html`**, no 500, no other row changed. Asserted by 1.4-INT-003.
- **Still deferred to Epic 2** (consistent with 1.3): surfacing toggle/delete errors *in the browser*. htmx ignores non-2xx swaps and the `beforeSwap` handler is scoped to `#add-form`, so a delete 404 is not displayed. **AD-7 note for Epic 2:** route the error to a dedicated region — never swap it into `#todo-{id}` outerHTML (that would destroy a real row). Therefore E2E `1.X-E2E-002` (forced-error *message shown*) is Epic-2 work, not this story.

### Architecture guardrails (binding)

[Source: ARCHITECTURE-SPINE.md]

- **AD-4** route → DB write → response; **explicit commit**; templates never touch the DB.
- **AD-5** failed request → proper HTTP status + rendered error fragment (AC #3).
- **AD-7** the delete swap targets the stable `#todo-{id}` root; removal leaves `#todo-list` intact.

### Version-specific patterns

- `session.get(Todo, todo_id)` then `session.delete(todo)` + `session.commit()` (SQLAlchemy 2.0).
- Empty success response: `HTMLResponse("", status_code=200)` (already imported).
- HTMX button trigger defaults to `click` for `<button>` — no extra config.

### Scope boundaries (resist creep)

- **In scope:** delete a todo (+ its 404 path) and the full add→toggle→delete happy-path E2E.
- **Out of scope:** confirm-before-delete, undo, responsive/empty/loading/error-UX polish and the forced-error-display E2E (`1.X-E2E-002`) — all Epic 2. Editing text is a v1 non-goal. [Source: prd.md §5]
- **Epic 1 completion:** 1.4 is the final story. After it is `done`, Epic 1 can be marked `done` (manually) and the optional retrospective run.

### ATDD Artifacts

Red-phase scaffolds generated and skipped — **activate one per task** (remove `@pytest.mark.skip`), confirm RED, implement to GREEN.

- Checklist: `_bmad-output/test-artifacts/atdd-checklist-1-4-delete-a-todo.md`
- New scaffolds: `tests/integration/test_story_1_4_delete.py` (1.4-INT-001/002/003) + `tests/e2e/test_story_1_4_journey.py` (`1.X-E2E-001`) — integration RED-verified against the current app (no delete route).
- Regression: `tests/api/test_example_api.py::test_delete_missing_todo_is_handled` now hits the real route (≤404, not 500).

Contract pinned: `DELETE /todos/{id}` → present: `session.delete` + commit + **empty 200** (outerHTML swap removes the `<li>`); missing: **404 + `_error.html`**.

### Project Structure Notes

Extends existing files: `app/routes/todos.py` (+delete route), `app/templates/_todo_item.html` (+delete button). New tests: `tests/integration/test_story_1_4_delete.py`, `tests/e2e/test_story_1_4_journey.py`. No new files/deps. No conflicts.

### Testing

- **Framework:** pytest + `TestClient` (integration) / pytest-playwright (e2e). `make test` / `make test-e2e`. [Source: tests/README.md]
- **Designed coverage (this story)** [Source: test-design-epic-1.md]:
  - `1.4-INT-001` — delete removes row + returns removal response (FR-4/FR-8)
  - `1.4-INT-002` — deleted todo absent on reload (FR-4)
  - `1.4-INT-003` — delete nonexistent id → 404 + error fragment, no 500, other rows untouched (R3/AD-5)
  - `1.X-E2E-001` — full UJ-1 journey add→toggle→delete, no full reload (R2)
  - Regression: `test_example_api.py::test_delete_missing_todo_is_handled` now hits the real route.
- **Discipline:** deterministic, isolated; seed via `session_for`/`insert_todo`; assert row counts + element removal; assert 404 (not 500) for the bad-id path; Playwright auto-waiting for the journey swaps.
- **Done gate:** the three 1.4 integration scenarios + the delete example-api test + the journey E2E green + full `make test` / `make test-e2e` green.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-1.4]
- [Source: _bmad-output/planning-artifacts/prds/prd-nearform_python-2026-07-14/prd.md] (FR-4 delete; UJ-1)
- [Source: _bmad-output/planning-artifacts/architecture/architecture-nearform_python-2026-07-14/ARCHITECTURE-SPINE.md] (AD-4, AD-5, AD-7)
- [Source: _bmad-output/test-artifacts/test-design/test-design-epic-1.md] (1.4 scenarios; E2E `1.X-E2E-001`; risks R2/R3)
- [Source: _bmad-output/implementation-artifacts/1-3-mark-a-todo-complete-or-active-again.md] (toggle route/404 pattern, in-place swap, reuse map, deferred mutation-error UI)
- [Source: tests/README.md] (harness helpers, run commands)

## Dev Agent Record

### Agent Model Used

claude-opus-4-8 (BMad dev-story workflow)

### Debug Log References

- RED: activated 3 integration + 1 journey e2e scaffold → 3 integration failures (no delete route → 404).
- GREEN: after delete route + delete button → 1.4-INT-001/002/003 pass; delete example-api regression (`tests/api/test_example_api.py`) passes.
- Full suite: 29 passed, 3 skipped (e2e excluded); `make test-e2e` → **3 passed incl. the full add→toggle→delete journey** in a real browser.

### Completion Notes List

- All 4 ACs satisfied; the full UJ-1 journey (`1.X-E2E-001`) passes end-to-end in Chromium — the live verification for delete.
- **Third swap style:** delete returns an **empty 200** and the button uses `hx-swap="outerHTML"` on `#todo-{id}` → the `<li>` is removed (vs 1.2 append / 1.3 replace).
- **404 path** identical to toggle: `session.get` None → 404 + `_error.html`, no 500, no other row changed (asserted by 1.4-INT-003, seeding a real row).
- Reused everything (delete route mirrors toggle; `TodoClient.delete`, `_error.html`, `session_for`/`insert_todo`, e2e fixtures). No new files/deps.
- Consistent with the 1.3 review: mutation-error **UI display** remains deferred to Epic 2 (server 404 contract is correct); `1.X-E2E-002` not implemented here.
- **Epic 1 feature work complete** (add / view / toggle / delete). Epic 1 can be marked `done` and the optional retrospective run.

### File List

**Modified (application):**
- `app/routes/todos.py` (+`DELETE /todos/{id}`)
- `app/templates/_todo_item.html` (+delete button)

**New (tests, this story):**
- `tests/integration/test_story_1_4_delete.py`
- `tests/e2e/test_story_1_4_journey.py`

## Change Log

| Date | Change |
| --- | --- |
| 2026-07-17 | Implemented Story 1.4 (delete): `DELETE /todos/{id}` (delete + commit + empty 200; missing → 404 + `_error.html`) and a delete button in `_todo_item.html` with `outerHTML` removal swap. 1.4-INT-001/002/003 + delete regression + the full add→toggle→delete journey E2E green; 29 passed / 3 e2e. Completes Epic 1 feature work. Status → review. |
| 2026-07-17 | Code review: applied 4 patches — journey E2E no-reload guard (AC4) + `to_have_count(1)` robustness, delete-only-targeted-row test, sequential double-delete test (200 then 404). 5 deferred (mutation-error UI / concurrency / confirm-undo / empty-state / silent-500 → Epic 2 & multi-user), 3 dismissed. 31 passed + 3 e2e. Status → done. |
