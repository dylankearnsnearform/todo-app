---
workflowStatus: 'completed'
totalSteps: 5
stepsCompleted: ['step-01-detect-mode','step-02-load-context','step-03-risk-and-testability','step-04-coverage-plan','step-05-generate-output']
lastStep: 'step-05-generate-output'
nextStep: ''
lastSaved: '2026-07-15'
---

# Test Design: Epic 1 — A Working Todo App

**Date:** 2026-07-15
**Author:** Dylan
**Status:** Draft

---

## Executive Summary

**Scope:** Epic-level test design for Epic 1 (Stories 1.1–1.4) of the Todo App — a FastAPI + Jinja2 + HTMX + SQLite server-rendered monolith.

**Risk Summary:**

- Total risks identified: 8
- High-priority risks (≥6): 1
- Critical categories: DATA (durability), TECH (hypermedia contract, error paths)

**Coverage Summary:**

- P0 scenarios: 7 (~6–10 hours)
- P1 scenarios: 9 (~5–9 hours)
- P2 scenarios: 3 (~2–4 hours)
- P3 scenarios: 0
- Test harness (one-time): ~3–5 hours
- **Total effort:** ~16–28 hours (~2–4 days), including harness setup

**Shape:** 19 scenarios — 3 unit, 14 integration, 2 E2E. Deliberately integration-heavy ("test trophy"), appropriate for a hypermedia CRUD app: `TestClient` integration tests assert both behavior and returned-fragment structure, so most risk is caught below the browser and only one E2E happy-path is needed.

---

## Not in Scope

| Item | Reasoning | Mitigation |
| --- | --- | --- |
| Epic 2 (responsive layout, empty/loading/error UI polish) | Separate, lower-risk epic; will get its own lightweight coverage | Some overlap covered here (AD-5 error paths at integration/E2E) |
| Auth / multi-user | Explicit v1 non-goal (PRD) | AD-6 extensibility smoke test (1.1-INT-004) guards the door |
| Load / performance benchmarking | Personal-scale app; no meaningful load | PERF risk is low (R8); manual observation only |
| Contract testing (Pact) | Single monolith, no service boundaries | N/A |

---

## Risk Assessment

### High-Priority Risks (Score ≥6)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner | Timeline |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R1 | DATA | Todos don't actually survive restart — uncommitted write, or SQLite accidentally configured in-memory (`:memory:`). Silent loss; kills FR-9. | 2 | 3 | 6 | Restart durability integration test + config guard + explicit commit in write path | Dev | Before Story 1.1 done |

### Medium-Priority Risks (Score 3–4)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R2 | TECH | HTMX fragment/swap contract mismatch (AD-7) — route returns fragment with wrong id/target → UI doesn't update or duplicates rows. | 2 | 2 | 4 | Assert fragment structure (single root, `todo-<id>`) in integration; one E2E swap check | Dev |
| R3 | TECH | Mutating a nonexistent id (double-click delete, stale tab) → missing 404/error fragment, unhandled 500 (AD-5). | 2 | 2 | 4 | Integration tests on toggle/delete of bad ids assert 404 + error fragment | Dev |

### Low-Priority Risks (Score 1–2)

| Risk ID | Category | Description | Probability | Impact | Score | Action |
| --- | --- | --- | --- | --- | --- | --- |
| R4 | SEC | Stored XSS via description if autoescape disabled / `|safe` used. | 1 | 2 | 2 | Escaping test (1.2-INT-004) |
| R5 | BUS | Junk input — empty/whitespace or oversized description. | 2 | 1 | 2 | Validation tests (1.2-UNIT-001, 1.2-INT-003) |
| R6 | TECH | Extensibility violated (AD-6) — single-user assumption hard-coded. | 2 | 1 | 2 | Extensibility smoke (1.1-INT-004); code review |
| R7 | OPS | Schema init/drift — no migrations; model/DB divergence. | 1 | 2 | 2 | Monitor; Alembic deferred per spine |
| R8 | PERF | List render latency (FR-5). Trivial at personal scale. | 1 | 1 | 1 | Monitor; manual observation |

### Risk Category Legend

- **TECH**: Technical/architecture (integration, contracts, error handling)
- **SEC**: Security (data exposure, injection)
- **PERF**: Performance
- **DATA**: Data integrity (loss, corruption)
- **BUS**: Business/UX impact
- **OPS**: Operations (deployment, config, schema)

---

## NFR Planning

Epic-specific NFR thresholds and the evidence a later `nfr-assess` should consume. Not a final audit.

| NFR Category | Requirement / Threshold | Risk Link | Planned Validation | Evidence Needed |
| --- | --- | --- | --- | --- |
| Reliability / Durability | Zero data loss across process restart | R1 | Integration restart test (1.1-INT-003) | pytest integration report |
| Reliability / Error handling | Failed action → correct HTTP status + rendered error fragment; app stays usable (AD-5) | R3 | Integration failure-path tests + E2E error path | pytest / Playwright reports |
| Security | Todo descriptions HTML-escaped on render | R4 | Integration test with `<script>` payload (1.2-INT-004) | pytest report |
| Maintainability | Adheres to spine ADs; simple, extensible | R6 | Code review + coverage report | `bmad-code-review`, coverage report |
| Performance | "Instantaneous / well under a second" — no hard number | R8 | Manual observation only | N/A (not gated) |

**Unknown thresholds:** Performance latency target is UNKNOWN — the PRD gives no concrete number. Logged as CLARIFY-1; not guessed, not gated at hobby scope.

---

## Entry Criteria

- [ ] Story 1.1 scaffold merged (FastAPI app skeleton + `Todo` model + `db.py`)
- [ ] Test SQLite DB / fixture available (isolated per-test, auto-teardown)
- [ ] pytest + FastAPI `TestClient` installed; Playwright installed for the single E2E
- [ ] App runnable locally via uvicorn

## Exit Criteria

- [ ] All P0 tests passing (100%)
- [ ] All P1 tests passing or triaged (≥95%)
- [ ] R1 durability test green
- [ ] No open high-severity bugs
- [ ] App-code coverage ≥80%

---

## Test Coverage Plan

> P0/P1/P2/P3 denote **priority/risk**, not execution timing. Execution cadence is defined separately below.

### P0 (Critical)

**Criteria:** Blocks the core journey + high risk (≥6) or core-CRUD correctness + no workaround.

| Test ID | Requirement | Test Level | Risk Link | Owner | Notes |
| --- | --- | --- | --- | --- | --- |
| 1.1-INT-003 | Durability: create → dispose/reopen DB → still present | Integration | R1 | Dev | The high-risk test; gates Story 1.1 |
| 1.1-INT-001 | `GET /` → 200 with `#todo-list` container | Integration | — | Dev | FR-2 |
| 1.1-INT-002 | List newest-first; active + completed both shown | Integration | — | Dev | FR-2 |
| 1.2-INT-001 | Create → persists (active, ts) + fragment single root `todo-<id>` | Integration | R2 | Dev | FR-1, FR-8, AD-7 |
| 1.2-INT-002 | Created todo present on reload | Integration | R1 | Dev | FR-1 |
| 1.3-INT-001 | Toggle active→completed persists + completed marker in fragment | Integration | R2 | Dev | FR-3, AD-7 |
| 1.4-INT-001 | Delete removes row + returns removal response | Integration | — | Dev | FR-4, FR-8 |

**Total P0:** 7 tests, ~6–10 hours

### P1 (High)

**Criteria:** Important flows + medium risk (3–4) + common workflows.

| Test ID | Requirement | Test Level | Risk Link | Owner | Notes |
| --- | --- | --- | --- | --- | --- |
| 1.1-UNIT-001 | Config guard rejects `:memory:` for real DB path | Unit | R1 | Dev | Mitigation guard |
| 1.2-UNIT-001 | Empty/whitespace description rejected | Unit | R5 | Dev | FR-1 |
| 1.2-INT-003 | Empty POST → not created, validation message, no new row | Integration | R5 | Dev | FR-1 |
| 1.2-INT-004 | `<script>` description HTML-escaped in fragment | Integration | R4 | Dev | SEC |
| 1.3-INT-002 | Toggle completed→active (reversible, idempotent per target) | Integration | — | Dev | FR-3 |
| 1.3-INT-003 | Toggle nonexistent id → 404 + error fragment, no 500 | Integration | R3 | Dev | AD-5 |
| 1.4-INT-002 | Deleted todo absent on reload | Integration | — | Dev | FR-4 |
| 1.4-INT-003 | Delete nonexistent id → 404 + error fragment, no 500 | Integration | R3 | Dev | AD-5 |
| 1.X-E2E-001 | UJ-1 journey: open → add (instant) → toggle (styles done) → delete (removed), no full reload | E2E | R2 | Dev | FR-5, AD-7 |

**Total P1:** 9 tests, ~5–9 hours

### P2 (Medium)

**Criteria:** Secondary behavior + low risk (1–2) + edge cases.

| Test ID | Requirement | Test Level | Risk Link | Owner | Notes |
| --- | --- | --- | --- | --- | --- |
| 1.1-UNIT-002 | New `Todo` defaults: `completed=False`, `created_at` UTC set | Unit | — | Dev | Conventions |
| 1.1-INT-004 | Extensibility smoke: no hard single-user constraint blocks future owner column | Integration | R6 | Dev | AD-6 |
| 1.X-E2E-002 | Forced failed action → non-disruptive error, app still usable | E2E | R3 | Dev | AD-5 |

**Total P2:** 3 tests, ~2–4 hours

### P3 (Low)

None for this epic.

---

## Execution Strategy

Philosophy: run everything in PRs if it stays under ~15 minutes; defer only expensive/long-running suites.

- **Every PR:** all unit + integration + the single E2E happy-path (`1.X-E2E-001`). Comfortably under 15 min.
- **Nightly/Weekly:** none required — no performance, chaos, or large-dataset suites are justified at this scale.

---

## Resource Estimates

| Priority | Count | Total Hours (range) | Notes |
| --- | --- | --- | --- |
| P0 | 7 | ~6–10 | Includes durability fixture (restart) setup |
| P1 | 9 | ~5–9 | Standard route/validation coverage |
| P2 | 3 | ~2–4 | Simple scenarios |
| P3 | 0 | — | — |
| Harness (one-time) | — | ~3–5 | pytest + `TestClient` fixtures + Playwright for 1 E2E |
| **Total** | **19** | **~16–28** | **~2–4 days** |

### Prerequisites

**Test Data:**
- `todo` factory (create Todos with controllable description/status/timestamp)
- Isolated per-test SQLite DB fixture (temp file, auto-teardown) — a real file, not `:memory:`, to exercise durability

**Tooling:**
- pytest + FastAPI `TestClient` for unit/integration
- Playwright (Python) for the single E2E journey
- Coverage reporting (e.g. `coverage.py` / `pytest-cov`)

**Environment:**
- Local uvicorn run for E2E
- Temp filesystem path for the durability test's SQLite file

---

## Quality Gate Criteria

### Pass/Fail Thresholds
- **P0 pass rate:** 100% (no exceptions)
- **P1 pass rate:** ≥95% (waivers required for failures)
- **P2 pass rate:** ≥90% (informational)
- **High-risk mitigations:** R1 complete before Story 1.1 → done

### Coverage Targets
- App-code coverage ≥80%
- Security scenario (escaping) present and passing
- Core CRUD + durability paths covered

### Non-Negotiable
- [ ] All P0 tests pass
- [ ] R1 (durability) mitigated and verified
- [ ] Escaping (SEC) test passes
- [ ] Planned NFR evidence exists (or `nfr-assess` records CONCERNS/waivers)

---

## Mitigation Plans

### R1: Todos don't survive restart (Score: 6)

**Mitigation Strategy:**
1. Write an integration test (`1.1-INT-003`) that creates Todos, disposes the SQLAlchemy engine (or re-opens a fresh session/engine against the same file), and asserts the Todos are still present.
2. Add a config guard that rejects `:memory:` (or a missing file path) for the real runtime database.
3. Ensure every write path (create/toggle/delete) commits the transaction explicitly.

**Owner:** Dev
**Timeline:** Before Story 1.1 is marked done
**Status:** Planned
**Verification:** `1.1-INT-003` green in CI; manual restart of local server preserves data.

---

## Assumptions and Dependencies

### Assumptions
1. v1 is single-user, single shared SQLite store (per PRD/spine).
2. Performance is validated by manual observation only (no hard latency target — CLARIFY-1).
3. Storage engine is SQLite via SQLAlchemy 2.0 (spine seed; confirm at implementation).

### Dependencies
1. Story 1.1 scaffold merged before integration/E2E suites can run.
2. Playwright installed before `1.X-E2E-001`/`-002`.

### Risks to Plan
- **Risk:** Estimates assume simple fixtures; a fiddly HTMX E2E setup could inflate the E2E cost.
  - **Impact:** +1–2 hours
  - **Contingency:** If E2E proves flaky, downgrade `1.X-E2E-002` (P2) to manual and keep the single P1 journey.

---

## Follow-on Workflows (Manual)

- Run `bmad-testarch-atdd` to generate the failing P0 tests before implementing Story 1.1 (ATDD red phase).
- Run `bmad-testarch-framework` if the pytest/Playwright harness isn't set up yet.
- Run `bmad-testarch-automate` for broader coverage once implementation exists.

---

## Open Clarifications

- **CLARIFY-1 (PERF):** Define a concrete latency target for action feedback, or formally accept "manual observation only" for hobby scope.

---

## Appendix

### Knowledge Base References
- `risk-governance.md` — risk classification framework
- `probability-impact.md` — risk scoring methodology
- `test-levels-framework.md` — test level selection
- `test-priorities-matrix.md` — P0–P3 prioritization

### Related Documents
- PRD: `_bmad-output/planning-artifacts/prds/prd-nearform_python-2026-07-14/prd.md`
- Epic/Stories: `_bmad-output/planning-artifacts/epics.md`
- Architecture: `_bmad-output/planning-artifacts/architecture/architecture-nearform_python-2026-07-14/ARCHITECTURE-SPINE.md`

---

**Generated by:** BMad TEA Agent — Test Architect Module
**Workflow:** `bmad-testarch-test-design`
