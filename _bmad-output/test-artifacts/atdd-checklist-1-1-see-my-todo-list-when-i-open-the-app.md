---
stepsCompleted: ['step-01-preflight-and-context', 'step-02-generation-mode', 'step-03-test-strategy', 'step-04c-aggregate', 'step-05-validate-and-complete']
lastStep: 'step-05-validate-and-complete'
generatedTestFiles:
  - 'tests/unit/test_story_1_1_scaffold.py'
  - 'tests/integration/test_story_1_1_list_view.py'
  - 'tests/support/db.py'
workflowStatus: 'completed'
lastSaved: '2026-07-17'
storyId: '1.1'
storyKey: '1-1-see-my-todo-list-when-i-open-the-app'
storyFile: '_bmad-output/implementation-artifacts/1-1-see-my-todo-list-when-i-open-the-app.md'
atddChecklistPath: '_bmad-output/test-artifacts/atdd-checklist-1-1-see-my-todo-list-when-i-open-the-app.md'
inputDocuments:
  - '_bmad-output/implementation-artifacts/1-1-see-my-todo-list-when-i-open-the-app.md'
  - '_bmad-output/test-artifacts/test-design/test-design-epic-1.md'
  - '_bmad-output/planning-artifacts/architecture/architecture-nearform_python-2026-07-14/ARCHITECTURE-SPINE.md'
  - 'tests/README.md'
  - '_bmad/tea/config.yaml'
---

# ATDD Checklist — Story 1.1: See my todo list when I open the app

## Step 1 — Preflight & Context

**Detected stack:** fullstack (Python FastAPI + hypermedia UI).

**Prerequisites:** all satisfied.
- Story 1.1 approved with clear ACs (status `ready-for-dev`).
- Test framework configured: pytest + FastAPI TestClient (`pyproject.toml`
  `[tool.pytest.ini_options]`, markers unit/integration/api/e2e) and
  pytest-playwright for E2E (`tests/` harness).
- Dev env available (venv with `.[test]` installed; Chromium installed).

**TEA config flags:**
- `tea_use_playwright_utils: true` → Node package, N/A for Python; principles
  already ported into the harness (`tests/support/`).
- `tea_use_pactjs_utils: false`; `tea_pact_mcp: none` → no contract testing.
- `tea_browser_automation: auto`; `test_stack_type: auto`.

**Existing patterns to REUSE (do not duplicate):**
- `tests/conftest.py` — `client` fixture (throwaway **file** SQLite DB, per-test),
  `test_db_url`/`test_db_path`/`app_env` fixtures, e2e auto-exclusion.
- `tests/support/clients.py` — `TodoClient` (`list_page`, `create`, `toggle`, `delete`).
- `tests/support/fragments.py` — `assert_list_container`, `assert_single_item_fragment` (AD-7).
- `tests/support/factories.py` — `todo_payload`, `todo_record`, `seed_descriptions`.
- `tests/e2e/conftest.py` — session-scoped `live_server`, `base_url`, `network_monitor`.

**Story 1.1 acceptance criteria (loaded):**
1. App scaffold serves `GET /` with `#todo-list` container, no login (FR-2, AD-7).
2. Persisted todos render newest-first; active + completed both shown (FR-2).
3. Durability across restart / engine dispose-reopen (FR-9; R1 — done gate).
4. No hard single-user assumption; owner column addable later (AD-6; R6).

**Designed scenarios (from test-design-epic-1.md) to scaffold red:**
| ID | Level | Priority | AC | Risk |
| --- | --- | --- | --- | --- |
| 1.1-UNIT-001 | unit | P0 | 3 | R1 — config guard rejects `:memory:` |
| 1.1-UNIT-002 | unit | P1 | 2 | — Todo defaults (`completed=False`, UTC `created_at`) |
| 1.1-INT-001 | integration | P0 | 1 | — `GET /` 200 + `#todo-list` |
| 1.1-INT-002 | integration | P1 | 2 | — newest-first, active+completed shown |
| 1.1-INT-003 | integration | P0 | 3 | R1 — durability across dispose/reopen (**done gate**) |
| 1.1-INT-004 | integration | P2 | 4 | R6 — extensibility smoke (AD-6) |

**Knowledge applied:** data-factories, test-quality (deterministic/isolated/no hard
waits/self-cleaning), test-levels-framework + test-priorities-matrix (already
encoded in the test-design).

## Step 2 — Generation Mode

**Mode: AI Generation** (recording skipped).

Rationale: greenfield ATDD (no app yet → nothing to record); ACs are clear and
standard (read/list + persistence); 5 of 6 scenarios are unit/integration via
`TestClient`. Recording only applies to live-browser verification of complex UI.
Generate from story ACs + test-design + architecture spine.

## Step 3 — Test Strategy

**Red-phase model (per skill contract):** each scenario is emitted as a
`@pytest.mark.skip` scaffold asserting **expected** behavior. The dev **activates
one per task** (removes the skip): activated test fails (RED) until implemented,
then passes (GREEN). Reuses the harness `client` fixture + `app_env`/`test_db_url`
fixtures + `TodoClient`/`fragments`/`factories` helpers (no duplication).

Lifecycle: **SKIP scaffold** (now) → **RED** (activated, unimplemented) →
**GREEN** (implemented). A skip must never be read as done; the P0 durability
test (1.1-INT-003) must be GREEN to satisfy the story's done-gate.

| AC | Scenario | ID | Level | Pri | Distinct because |
| --- | --- | --- | --- | --- | --- |
| 1 | `GET /` 200, `#todo-list`, no login, zero-todos boundary | 1.1-INT-001 | integration | P0 | route+template render |
| 2 | newest-first; active+completed both shown | 1.1-INT-002 | integration | P1 | DB query + render |
| 3 | durability: create → dispose/reopen → present | 1.1-INT-003 | integration | P0 | real file persistence (R1 gate) |
| 3 | config guard rejects `:memory:`; default file URL | 1.1-UNIT-001 | unit | P0 | pure guard logic |
| 2 | `Todo` defaults completed=False, created_at UTC | 1.1-UNIT-002 | unit | P1 | pure model defaults |
| 4 | extensibility smoke — no hard single-user (AD-6) | 1.1-INT-004 | integration | P2 | schema/insert (R6) |

**No E2E for 1.1** (browser swap = 1.2; would duplicate INT-001). Negative/edge
for high-risk R1: `:memory:` guard + default-file assertion + dispose/reopen test.
All tests designed to FAIL before implementation (verified in step 4).

## Step 4 — Generated Red-Phase Scaffolds

**Mode:** sequential (API/backend worker acted as generator; E2E worker empty — no
E2E for 1.1). All scaffolds `@pytest.mark.skip` asserting expected behavior; no
placeholder assertions.

**Files written:**
- `tests/unit/test_story_1_1_scaffold.py` — 1.1-UNIT-001 (×2: reject `:memory:` +
  default-is-file), 1.1-UNIT-002 (Todo defaults).
- `tests/integration/test_story_1_1_list_view.py` — 1.1-INT-001..004.
- `tests/support/db.py` — shared seeding helper (`session_for`, `insert_todo`) —
  fixture infrastructure for direct persistence before create routes exist.

**Test count:** 7 functions across 6 scenarios (all skipped).

## Step 4 — TDD Red-Phase Compliance ✅

- All 7 collect cleanly and skip with clear `[Pn] <ID> — activate when …` reasons.
- No placeholder assertions; every test asserts real expected behavior.
- **Activation check (RED→GREEN):** activated copies run against a throwaway
  correct-implementation stub → **7/7 GREEN**; against no/partial impl → RED.
  Proves the scaffolds are satisfiable and correctly specify the story.
- Stub + temp copies discarded; repo left with scaffolds only; default `pytest`
  stays green (1 passed, 15 skipped).

**Bug caught & fixed by the activation check:** 1.1-UNIT-002 originally asserted
`created_at.tzinfo is not None`, but **SQLite does not preserve tz-awareness** —
the value reads back naive. Relaxed to verify a fresh UTC timestamp by value
proximity (spine requires *stored* UTC, achievable on SQLite).

## Acceptance Criteria Coverage

| AC | Scenario(s) | Status |
| --- | --- | --- |
| 1 — serves `/` + `#todo-list`, no login | 1.1-INT-001 | scaffolded (skip) |
| 2 — newest-first, active+completed; Todo defaults | 1.1-INT-002, 1.1-UNIT-002 | scaffolded (skip) |
| 3 — durability + `:memory:` guard | 1.1-INT-003, 1.1-UNIT-001 | scaffolded (skip) |
| 4 — AD-6 extensibility | 1.1-INT-004 | scaffolded (skip) |

## Step 5 — Validation & Handoff

Validated against `checklist.md`: prerequisites satisfied; test files created &
verified red-phase; checklist matches ACs; story metadata + handoff paths captured;
no orphaned browsers/CLI sessions; temp artifacts under `_bmad-output/test-artifacts/`.

**Key assumptions/contract pinned by the scaffolds (dev must honour):**
- `app.db.resolve_database_url() -> str` (env `DATABASE_URL`, file fallback, raises
  `ValueError` on in-memory).
- `app.db.Base`, `app.db.init_db()`, `app.db.SessionLocal`; `app.models.Todo`
  (`__tablename__="todos"`, `completed` default False, `created_at` default UTC).
- `app.main:app` with lifespan schema init; `GET /` renders `#todo-list` with items
  `id="todo-<id>"`, ordered newest-first, showing active + completed.

**Activation workflow for the dev:** remove `@pytest.mark.skip` per task → confirm
RED → implement → GREEN. The P0 durability test (1.1-INT-003) must be GREEN to
close the story's done-gate.

**Next workflow:** `dev-story` (Amelia). Run `bmad-testarch-automate` only after
implementation (green phase) to expand coverage.
