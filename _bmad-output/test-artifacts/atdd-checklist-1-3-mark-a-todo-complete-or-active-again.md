---
stepsCompleted: ['step-01-preflight-and-context', 'step-02-generation-mode', 'step-03-test-strategy', 'step-04c-aggregate', 'step-05-validate-and-complete']
lastStep: 'step-05-validate-and-complete'
lastSaved: '2026-07-17'
storyId: '1.3'
storyKey: '1-3-mark-a-todo-complete-or-active-again'
storyFile: '_bmad-output/implementation-artifacts/1-3-mark-a-todo-complete-or-active-again.md'
atddChecklistPath: '_bmad-output/test-artifacts/atdd-checklist-1-3-mark-a-todo-complete-or-active-again.md'
generatedTestFiles:
  - 'tests/integration/test_story_1_3_toggle.py'
workflowStatus: 'completed'
inputDocuments:
  - '_bmad-output/implementation-artifacts/1-3-mark-a-todo-complete-or-active-again.md'
  - '_bmad-output/test-artifacts/test-design/test-design-epic-1.md'
  - '_bmad-output/planning-artifacts/architecture/architecture-nearform_python-2026-07-14/ARCHITECTURE-SPINE.md'
---

# ATDD Checklist — Story 1.3: Mark a todo complete or active again

## Step 1 — Preflight & Context

- Stack fullstack; prereqs satisfied; story 1.3 `ready-for-dev`.
- Reuse (no duplication): `TodoClient.toggle()`, `assert_single_item_fragment`, `session_for`/`insert_todo`, `client`/`test_db_url`. `_todo_item.html`, `_error.html`, WAL/`get_session` all from 1.1/1.2.

## Step 2 — Generation Mode

AI generation (standard toggle CRUD + error path).

## Step 3 — Test Strategy (no duplicate coverage)

| Scenario | ID | Level | Pri | Where |
| --- | --- | --- | --- | --- |
| toggle active→completed persists + completed marker in fragment | 1.3-INT-001 | integration | P0 | **new** `test_story_1_3_toggle.py` |
| toggle completed→active (reversible) | 1.3-INT-002 | integration | P1 | **new** |
| toggle nonexistent id → 404 + error fragment, no 500 | 1.3-INT-003 | integration | P1 | **new** (stronger than the looser `test_example_api.py` toggle test, which stays as regression) |

- No new unit scenario (toggle is a trivial flip). No dedicated 1.3 E2E — the toggle step is covered by the full add→toggle→delete journey (`1.X-E2E-001`) that completes in Story 1.4.
- Red-phase model: `@pytest.mark.skip` scaffolds; dev activates one per task.

## Step 4 — Generated Scaffolds + Red-Phase Compliance ✅

- **File:** `tests/integration/test_story_1_3_toggle.py` — 3 skipped scaffolds; strong assertions (AD-7 single-root fragment, `class="todo-item completed"` marker, DB `completed` value, 404 + `role="alert"` fragment).
- Collect + skip cleanly; no placeholder assertions.
- **RED verified:** temporarily activated against the current app (no toggle route) → **3/3 failed** for the right reasons (toggle → 404 route-not-found; the bad-id test correctly rejects FastAPI's default `{"detail":"Not Found"}` for lacking the rendered error fragment). Reverted to skipped; full default suite green (22 passed, 5 skipped).

## Step 5 — Validation & Handoff

- Contract pinned by the scaffolds: `POST /todos/{id}/toggle` → present: flip `completed`, commit, return `_todo_item.html` (single root `todo-<id>`, `completed` marker reflects new state); missing: **404 + `_error.html`** (no 500).
- **Done gate:** 3 scaffolds green + `test_example_api.py` toggle test green + `make test` green.
- **Next workflow:** `dev-story`.
