---
stepsCompleted: ['step-01-preflight-and-context', 'step-02-generation-mode', 'step-03-test-strategy', 'step-04c-aggregate', 'step-05-validate-and-complete']
lastStep: 'step-05-validate-and-complete'
lastSaved: '2026-07-17'
storyId: '1.4'
storyKey: '1-4-delete-a-todo'
storyFile: '_bmad-output/implementation-artifacts/1-4-delete-a-todo.md'
atddChecklistPath: '_bmad-output/test-artifacts/atdd-checklist-1-4-delete-a-todo.md'
generatedTestFiles:
  - 'tests/integration/test_story_1_4_delete.py'
  - 'tests/e2e/test_story_1_4_journey.py'
workflowStatus: 'completed'
inputDocuments:
  - '_bmad-output/implementation-artifacts/1-4-delete-a-todo.md'
  - '_bmad-output/test-artifacts/test-design/test-design-epic-1.md'
  - '_bmad-output/planning-artifacts/architecture/architecture-nearform_python-2026-07-14/ARCHITECTURE-SPINE.md'
---

# ATDD Checklist — Story 1.4: Delete a todo

## Step 1 — Preflight & Context

- Stack fullstack; prereqs satisfied; story 1.4 `ready-for-dev` (last in Epic 1).
- Reuse (no duplication): `TodoClient.delete()`, `session_for`/`insert_todo`, `_todo_count`, `client`/`test_db_url`, e2e `page`/`base_url`/`network_monitor`. `_error.html` (404 path), item template all from 1.1–1.3.

## Step 2 — Generation Mode

AI generation (delete mirrors the toggle route/404 pattern; journey E2E is a standard flow).

## Step 3 — Test Strategy (no duplicate coverage)

| Scenario | ID | Level | Pri | Where |
| --- | --- | --- | --- | --- |
| delete removes row + empty removal response | 1.4-INT-001 | integration | P0 | **new** `test_story_1_4_delete.py` |
| deleted todo absent on reload | 1.4-INT-002 | integration | P1 | **new** |
| delete nonexistent id → 404 + error fragment, no 500, others untouched | 1.4-INT-003 | integration | P1 | **new** (stronger than the looser `test_example_api.py` delete test, kept as regression) |
| full UJ-1 journey: open → add → toggle → delete, no reload | 1.X-E2E-001 | e2e | P1 | **new** `test_story_1_4_journey.py` |

- No new unit scenario (delete is a get-then-delete). `1.X-E2E-002` (forced-error *display*) is Epic 2 (mutation-error UI deferred).
- Red-phase model: `@pytest.mark.skip` scaffolds; dev activates per task.

## Step 4 — Generated Scaffolds + Red-Phase Compliance ✅

- **Files:** `tests/integration/test_story_1_4_delete.py` (3 scaffolds) + `tests/e2e/test_story_1_4_journey.py` (1 journey scaffold). All skipped; strong assertions (empty removal response + DB count, absent-on-reload, 404 + `role="alert"` + other rows untouched; journey drives add→toggle→delete via HTMX with a clean network monitor).
- Collect + skip cleanly; no placeholder assertions.
- **RED verified (integration):** temporarily activated against the current app (no delete route) → **3/3 failed** for the right reasons (delete → 404 no-route; bad-id rejects FastAPI's default `{"detail":"Not Found"}`). Reverted; full default suite green (26 passed, 6 skipped). The journey E2E is red until the delete control exists (reasoned, not run — it's slow).

## Step 5 — Validation & Handoff

- Contract pinned: `DELETE /todos/{id}` → present: `session.delete` + commit + **empty 200** (outerHTML swap removes the `<li>`); missing: **404 + `_error.html`**. Delete button in `_todo_item.html`: `hx-delete`, `hx-target="#todo-{id}"`, `hx-swap="outerHTML"`.
- **Done gate (1.4 / Epic 1):** 3 integration scenarios + delete example-api test + journey E2E green + `make test` / `make test-e2e` green.
- **Next workflow:** `dev-story` (completes Epic 1's feature work).
