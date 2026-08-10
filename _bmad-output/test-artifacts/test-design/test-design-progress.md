---
workflowStatus: 'completed'
totalSteps: 5
stepsCompleted: ['step-01-detect-mode', 'step-02-load-context', 'step-03-risk-and-testability', 'step-04-coverage-plan', 'step-05-generate-output']
lastStep: 'step-05-generate-output'
nextStep: ''
lastSaved: '2026-07-15'
inputDocuments:
  - _bmad-output/planning-artifacts/epics.md
  - _bmad-output/planning-artifacts/architecture/architecture-nearform_python-2026-07-14/ARCHITECTURE-SPINE.md
  - _bmad-output/planning-artifacts/prds/prd-nearform_python-2026-07-14/prd.md
  - knowledge/risk-governance.md
  - knowledge/probability-impact.md
  - knowledge/test-levels-framework.md
  - knowledge/test-priorities-matrix.md
---

# Test Design Progress — nearform_python (Todo App)

## Step 1: Mode Detection

- **Mode:** Epic-Level
- **Target:** Epic 1 — "A Working Todo App" (Stories 1.1–1.4)
- **Rationale:** Both PRD/architecture and epics/stories exist, but the project is a small 6-story app on a fully-settled architecture — system-level QA strategy would be over-engineering. Risk concentrates in Epic 1 (persistence durability, CRUD correctness, HTMX mutation/swap contract). Epic 2 is lower-risk polish.
- **Inputs available:**
  - Epic + stories with ACs: `_bmad-output/planning-artifacts/epics.md`
  - Architecture context: `_bmad-output/planning-artifacts/architecture/architecture-nearform_python-2026-07-14/ARCHITECTURE-SPINE.md`
  - PRD: `_bmad-output/planning-artifacts/prds/prd-nearform_python-2026-07-14/prd.md`

## Step 2: Context Loaded

- **detected_stack:** backend (Python/FastAPI + server-rendered HTMX; no JS build, no frontend framework)
- **Config flags:** playwright_utils=true, pactjs_utils=false, pact_mcp=none, browser_automation=auto, test_stack_type=auto
- **Contract testing:** not applicable (single monolith, no service boundaries)
- **Browser exploration:** skipped (nothing scaffolded/running yet); relying on doc analysis
- **Existing app tests:** none
- **Knowledge fragments:** risk-governance, probability-impact, test-levels-framework, test-priorities-matrix

## Step 3: Risk & Testability Assessment

Epic-Level mode — system-level testability review skipped.

### Risk Register (Epic 1)

| ID | Cat | Risk | P | I | Score | Level |
|----|-----|------|---|---|-------|-------|
| R1 | DATA | Todos don't survive restart (uncommitted write / in-memory SQLite). Kills FR-9, silent loss. | 2 | 3 | 6 | HIGH |
| R2 | TECH | HTMX fragment/swap contract mismatch (AD-7) → no update or duplicated rows (FR-5). | 2 | 2 | 4 | Med |
| R3 | TECH | Mutating nonexistent id → missing 404/error fragment, unhandled 500 (AD-5). | 2 | 2 | 4 | Med |
| R4 | SEC | Stored XSS via description if autoescape disabled / |safe used. | 1 | 2 | 2 | Low |
| R5 | BUS | Junk input (empty/whitespace/huge description) — FR-1 validation. | 2 | 1 | 2 | Low |
| R6 | TECH | Extensibility violated (AD-6) — single-user assumption hard-coded. | 2 | 1 | 2 | Low |
| R7 | OPS | Schema init/drift — no migrations; model/DB divergence. | 1 | 2 | 2 | Low |
| R8 | PERF | List render latency (FR-5). Trivial at personal scale. | 1 | 1 | 1 | Low |

### HIGH Risk Mitigation

- **R1 (DATA, 6):** Owner = dev (Story 1.1). Mitigation: (a) integration test that persists a todo, disposes the engine / re-opens the DB, and asserts the todo is still present; (b) config guard rejecting `:memory:` for the real DB path; (c) explicit commit in every write path. Timeline: must pass before Story 1.1 is marked done.

### NFR Planning

| NFR | Category | Threshold | Evidence |
|-----|----------|-----------|----------|
| Durability | DATA | Zero data loss across restart | Integration restart test |
| Error handling | TECH/OPS | Failed action → HTTP status + error fragment, app usable (AD-5) | Integration failure-path tests |
| Security | SEC | Descriptions HTML-escaped on render | Unit/integration `<script>` payload test |
| Performance | PERF | UNKNOWN — no hard number in PRD | Manual observation; flagged clarification (low priority) |
| Maintainability | TECH | Adheres to spine ADs; simple | Code review |

### Open Clarifications
- CLARIFY-1 (PERF): Define a concrete latency target for action feedback, or accept "manual observation only" for hobby scope.

## Step 4: Coverage Plan & Execution Strategy

### Coverage Matrix (18 scenarios: 4 unit, 12 integration, 2 E2E)

| Test ID | Scenario | Level | Pri | Covers |
|---------|----------|-------|-----|--------|
| 1.1-INT-003 | Durability: create → dispose/reopen DB → present | Integration | P0 | FR-9, R1 |
| 1.1-UNIT-001 | Config guard rejects :memory: for real DB | Unit | P1 | R1 |
| 1.1-INT-001 | GET / → 200 with #todo-list container | Integration | P0 | FR-2 |
| 1.1-INT-002 | List newest-first, active+completed shown | Integration | P0 | FR-2 |
| 1.1-UNIT-002 | New Todo defaults completed=False, created_at UTC | Unit | P2 | conventions |
| 1.1-INT-004 | Extensibility smoke: no hard single-user constraint | Integration | P2 | R6, AD-6 |
| 1.2-INT-001 | Create → persists + fragment single root todo-<id> | Integration | P0 | FR-1, FR-8, R2/AD-7 |
| 1.2-INT-002 | Created present on reload | Integration | P0 | FR-1 |
| 1.2-UNIT-001 | Empty/whitespace description rejected | Unit | P1 | FR-1, R5 |
| 1.2-INT-003 | Empty POST → not created, message, no row | Integration | P1 | FR-1, R5 |
| 1.2-INT-004 | XSS: <script> description HTML-escaped | Integration | P1 | SEC, R4 |
| 1.3-INT-001 | Toggle active→completed persists + marker | Integration | P0 | FR-3, R2/AD-7 |
| 1.3-INT-002 | Toggle completed→active reversible/idempotent | Integration | P1 | FR-3 |
| 1.3-INT-003 | Toggle bad id → 404 + error fragment, no 500 | Integration | P1 | AD-5, R3 |
| 1.4-INT-001 | Delete removes row + removal response | Integration | P0 | FR-4, FR-8 |
| 1.4-INT-002 | Deleted absent on reload | Integration | P1 | FR-4 |
| 1.4-INT-003 | Delete bad id → 404 + error fragment, no 500 | Integration | P1 | AD-5, R3 |
| 1.X-E2E-001 | UJ-1 journey: add/toggle/delete, no full reload | E2E | P1 | FR-5, R2/AD-7 |
| 1.X-E2E-002 | Forced failed action → non-disruptive error, usable | E2E | P2 | AD-5 |

### NFR Coverage & Evidence Plan
- Durability (DATA/R1): 1.1-INT-003 → pytest integration report (consumed later by nfr-assess).
- Error handling (AD-5): 1.3-INT-003, 1.4-INT-003, 1.X-E2E-002 → pytest/Playwright reports.
- Security (SEC/R4): 1.2-INT-004 → pytest report.
- Performance (PERF): threshold UNKNOWN → no automated gate (assumption: manual observation for hobby scope). Not a blocker.
- Maintainability (TECH): bmad-code-review + CI lint (not a test scenario).

### Execution Strategy
- PR (every push): all unit + integration + 1.X-E2E-001. Target < 15 min.
- Nightly/Weekly: none required at hobby scale.

### Resource Estimates (ranges)
- Framework harness (pytest + TestClient fixtures + Playwright 1 E2E): ~3-5 h one-time
- P0 (8): ~6-10 h | P1 (7): ~5-9 h | P2 (3): ~2-4 h | P3: none
- Total incl. harness: ~16-28 h

### Quality Gates
- P0 pass rate = 100%
- P1 pass rate >= 95%
- R1 durability test (1.1-INT-003) green before Story 1.1 done
- App-code coverage >= 80%
- NFR evidence identified for durability, error handling, security (final PASS/FAIL deferred to nfr-assess)

## Step 5: Output Generated & Validated

- **Mode:** Epic-Level (sequential, single artifact)
- **Output:** _bmad-output/test-artifacts/test-design/test-design-epic-1.md
- **Checklist validation (epic-level):**
  - Risks genuine, categorized, P/I in 1-3, scores = P*I, 1 high (>=6) flagged with mitigation+owner+timeline — PASS
  - NFR planning present; unknown PERF threshold marked UNKNOWN (not guessed), converted to CLARIFY-1 — PASS
  - ACs decomposed to atomic scenarios; levels favor unit>integration>E2E; no duplicate coverage — PASS
  - Priorities assigned; P0 = 7 (<40% and meets strict criteria); execution strategy simple PR/nightly — PASS
  - Estimates as ranges (no false precision) — PASS
  - Quality gates defined (P0 100%, P1 >=95%, coverage >=80%) — PASS
  - Correction applied: recounted to 19 scenarios (3 unit / 14 integration / 2 E2E)
- **No orphaned browser sessions** (browser exploration was skipped; none opened)
- **Artifacts stored under _bmad-output/test-artifacts/**
