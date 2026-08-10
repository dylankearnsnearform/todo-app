---
stepsCompleted: ['step-01-preflight-and-context', 'step-02-generation-mode', 'step-03-test-strategy', 'step-04c-aggregate', 'step-05-validate-and-complete']
lastStep: 'step-05-validate-and-complete'
lastSaved: '2026-07-17'
storyId: '1.2'
storyKey: '1-2-add-a-new-todo'
storyFile: '_bmad-output/implementation-artifacts/1-2-add-a-new-todo.md'
atddChecklistPath: '_bmad-output/test-artifacts/atdd-checklist-1-2-add-a-new-todo.md'
generatedTestFiles:
  - 'tests/integration/test_story_1_2_create.py'
workflowStatus: 'completed'
inputDocuments:
  - '_bmad-output/implementation-artifacts/1-2-add-a-new-todo.md'
  - '_bmad-output/test-artifacts/test-design/test-design-epic-1.md'
  - '_bmad-output/planning-artifacts/architecture/architecture-nearform_python-2026-07-14/ARCHITECTURE-SPINE.md'
  - 'tests/README.md'
---

# ATDD Checklist — Story 1.2: Add a new todo

## Step 1 — Preflight & Context

- **Stack:** fullstack (FastAPI + hypermedia). Prereqs satisfied; story 1.2 `ready-for-dev` with clear ACs; harness configured.
- **Reuse (do not duplicate):** `TodoClient.create()` (posts form to `/todos`), `assert_single_item_fragment` (AD-7), `todo_payload` factory, `client`/`test_db_url` fixtures, `tests/support/db.py` (`session_for`), e2e `live_server`/`network_monitor`. App contract + `is_valid_description`, `_todo_item.html`, `_error.html` all exist from Story 1.1.

## Step 2 — Generation Mode

**AI generation** (recording skipped): standard CRUD create path; assertions are clear from ACs + test-design.

## Step 3 — Test Strategy (no duplicate coverage)

| Scenario | ID | Level | Pri | Where |
| --- | --- | --- | --- | --- |
| create persists (active, ts) + single-root `todo-<id>` fragment | 1.2-INT-001 | integration | P0 | **new** `test_story_1_2_create.py` |
| created todo present on reload | 1.2-INT-002 | integration | P1 | **new** |
| empty/whitespace POST → 422 + validation fragment + no new row | 1.2-INT-003 | integration | P1 | **new** |
| `<script>` escaped in returned fragment | 1.2-INT-004 | integration | P1 | **new** |
| empty/whitespace rejected (`is_valid_description`) | 1.2-UNIT-001 | unit | P1 | **already green** — `test_example_unit.py::test_description_validation` (not duplicated) |
| create-and-see swap (browser) | epic E2E | e2e | P1 | **existing scaffold** — `test_example_e2e.py::test_create_todo_shows_in_list` (activate in dev-story) |

Red-phase model: `@pytest.mark.skip` scaffolds asserting expected behavior; dev activates one per task (skip → RED → GREEN). The three example tests deferred from 1.1 (create fragment, escaping, e2e swap) are also activated in dev-story.

## Step 4 — Generated Scaffolds + Red-Phase Compliance ✅

- **File:** `tests/integration/test_story_1_2_create.py` — 4 skipped scaffolds (1.2-INT-001..004), strong assertions (AD-7 single-root fragment, DB row counts, 422 + `role="alert"` error fragment, HTML escaping).
- Collect cleanly; all skip with clear `[Pn] <ID> — activate when …` reasons; no placeholder assertions.
- **RED verified:** temporarily activated against the current app (no `POST /todos` yet) → **4/4 failed** for the right reason (404; nothing persisted). Reverted to skipped. Full default suite stays green (13 passed, 7 skipped).
- GREEN satisfiability will be confirmed in `dev-story` when `POST /todos` is implemented (the scaffolds map directly to the create route + `_error.html` + `_todo_item.html`, all satisfiable).

## Step 5 — Validation & Handoff

- Contract pinned by the scaffolds (dev must honour): `POST /todos` accepts form `description`; valid → 200/201 + `_todo_item.html` fragment (single root `todo-<id>`), persisted `completed=False` + `created_at`, committed; invalid → **422** + `_error.html` fragment (`role="alert"`), no row inserted; descriptions autoescaped (no `| safe`).
- **Done gate (1.2):** all four new scaffolds green + the three activated example tests green + `make test` and `make test-e2e` green.
- **Next workflow:** `dev-story` (Amelia). `bmad-testarch-automate` only after green.
