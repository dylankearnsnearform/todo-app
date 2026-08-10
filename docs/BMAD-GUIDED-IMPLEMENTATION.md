# How BMAD Guided the Implementation

This documents how the **BMAD Method** (a set of AI-agent workflow "skills") drove
the build of the Todo App — from a PRD to a tested, containerized application — and
what that structure added over ad-hoc AI coding.

---

## 1. The artifact chain

BMAD produced a chain of artifacts where each one constrained the next, so decisions
made early were carried forward consistently instead of being re-litigated:

```
PRD ──► Architecture Spine ──► Epics + Stories ──► Test Design
                                      │
                    per story:  create-story ──► ATDD (red tests) ──► dev-story ──► code-review
```

| Artifact | Produced by | Role |
| --- | --- | --- |
| **PRD** (`planning-artifacts/prds/…/prd.md`) | (input) | FR-1..FR-9, non-goals, success metrics |
| **Architecture Spine** (`…/architecture/…/ARCHITECTURE-SPINE.md`) | Architect (Winston) | Binding invariants **AD-1..AD-7**, stack, source-tree seed |
| **Epics & Stories** (`…/epics.md`) | PM (John) | FR→epic mapping; BDD acceptance criteria per story |
| **Test Design** (`test-artifacts/test-design/…`) | Test Architect (Murat) | Risk-scored scenarios per story, tagged by level + priority |
| **Per-story files** (`implementation-artifacts/1-*.md`) | create-story | The dev's full context: reuse map, guardrails, tasks, references |

The **Architecture Spine** was the single most influential artifact. Its invariants
were cited in every subsequent step and prevented drift:
- **AD-1/AD-2** (hypermedia monolith, one process) → no SPA/JSON detours; shaped the whole test + Docker approach.
- **AD-3** (SQLite is sole source of truth) → the durability tests and the `:memory:` config guard.
- **AD-7** (fixed swap contract: `#todo-list`, `todo-<id>`) → made the three swap styles (append / replace / remove) interoperable across create, toggle, and delete.

---

## 2. The per-story loop (the core of the method)

Every story ran the same four-workflow loop. Each stage caught things the previous
one couldn't:

1. **`create-story`** — turned an epic entry into a self-contained spec. Its signature
   move was a **"reuse map"**: an explicit table of what already existed with an
   instruction to *extend, not recreate*. This directly prevented the classic AI
   failure of reinventing existing routes/templates/fixtures.
2. **`bmad-testarch-atdd`** — generated **red-phase acceptance tests first**
   (skipped scaffolds asserting expected behavior), verified they actually failed for
   the right reason, and pinned the route/response contract before any code existed.
3. **`bmad-dev-story`** — implemented against the red tests (red → green → refactor),
   updated the story's Dev Agent Record, and enforced a definition-of-done.
4. **`bmad-code-review`** — an **adversarial, multi-agent** review (three independent
   reviewers: a general defect hunter, an edge-case hunter, and an acceptance auditor),
   then triage into patch / defer / dismiss.

**Concrete payoffs from the structure:**
- ATDD's "verify the test is red against a stub" step **caught a bad test assertion**
  in Story 1.1 (asserting tz-aware `created_at` that SQLite can't store).
- code-review's independent auditors **found real gaps** every story (e.g. an
  untested reload-render path, a config-guard bypass, a global HTMX handler that would
  hijack future 404s) and, importantly, **correctly deferred** out-of-scope items
  rather than gold-plating.

---

## 3. How BMAD handled scope and change

- **Deferred backlog with rationale.** When code review found real-but-out-of-scope
  issues (mutation-error UI, concurrency, confirm/undo), BMAD recorded them in
  `deferred-work.md` mapped to the epic that will address them (mostly Epic 2 / FR-7),
  instead of expanding the current story. This kept the PRD's restraint value (SM-C1)
  intact while never losing a finding.
- **Sprint state as the source of truth.** `sprint-status.yaml` tracked each story
  through `backlog → ready-for-dev → in-progress → review → done`, and the workflows
  read/updated it — so "what's next" was always unambiguous.
- **A product decision was surfaced, not assumed.** The max-description-length question
  (a PRD open item) was raised as a *decision* during review rather than silently
  defaulted — the human chose 500 chars.

---

## 4. Where BMAD's generic templates needed human adaptation

BMAD's workflows are framework-agnostic and occasionally assume a JS/Node or
multi-service shape. Human/architectural judgment corrected these:
- The test-framework and ATDD skills assume `@seontechnologies/playwright-utils`
  (a Node library). This is a **Python** project, so the *principles* (fixture
  composition, factories, network-error monitoring) were ported to pytest +
  `pytest-playwright` instead.
- The containerization task template assumed **frontend + backend + database**
  containers. The real architecture (AD-1/AD-2/AD-3) is **one image + a SQLite
  volume** — recognizing that mismatch and adapting was a design decision, not a
  mechanical step.

---

## 5. What BMAD added over "just ask the AI to build it"

- **Traceability:** every line of code traces PRD → FR → AD → story → test → review.
- **Test-first by construction:** ATDD made red-before-green the default, not an afterthought.
- **Independent review:** the adversarial multi-agent pass caught issues a single
  generate-and-check pass would have shipped (notably a validation UX that was *green
  in tests but broken in the browser*).
- **Discipline:** explicit scope boundaries + a deferred backlog kept v1 from sprawling.

## 6. Limitations of the approach

- The same underlying model both wrote and reviewed the code; the adversarial
  structure helped, but a genuinely different reviewer would be stronger.
- BMAD orchestrates *process*, not *correctness* — the real bugs were still caught by
  **running the software** (live browser + Docker), which the human insisted on. Green
  BMAD workflows are necessary, not sufficient.
- The interactive Epic-1 retrospective was skipped; learnings live instead in the
  per-story records, `deferred-work.md`, and `AI-INTEGRATION-LOG.md`.

---

*See also:* `AI-INTEGRATION-LOG.md` (AI usage / MCP / limitations), `docs/QA-REPORT.md`
(coverage, accessibility, security, performance), and per-story records under
`_bmad-output/implementation-artifacts/`.
