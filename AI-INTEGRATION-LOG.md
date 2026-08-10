# AI Integration Documentation — Phase 3

Project: Todo App — server-rendered hypermedia monolith (FastAPI + Jinja2 + HTMX + SQLite).
Tooling: Claude Code (Opus 4.8) driving the **BMAD Method** workflow skills, plus direct engineering for infra.

> How to read this log: it records *how* AI assistance was used across Phase 3, what
> worked, and — deliberately — where it fell short and human judgment was required.
> Examples are concrete (real bugs, real files) so the claims are checkable.

---

## 1. Agent Usage

**Tasks completed with AI assistance (Epic 1 — a working Todo app + containerization):**

| Task | AI workflow used | Outcome |
| --- | --- | --- |
| Test framework setup | `bmad-testarch-framework` | pytest + FastAPI TestClient + Playwright harness, verified against a throwaway app stub |
| Story 1.1 View list (scaffold + SQLite) | create-story → atdd → dev-story → code-review | done |
| Story 1.2 Add a todo | create-story → atdd → dev-story → code-review | done |
| Story 1.3 Toggle complete/active | create-story → atdd → dev-story → code-review | done |
| Story 1.4 Delete a todo | create-story → atdd → dev-story → code-review | done |
| Containerization (Dockerfile / compose / health / env) | direct engineering (spine-deferred infra) | built + run + verified in real Docker |

End state: **32 unit/integration/api tests + 3 E2E, ~96% app coverage**, full add→view→toggle→delete journey passing in a real browser.

**Prompts / patterns that worked best:**
- **Structured multi-agent workflows over one big prompt.** The BMAD loop (create-story → ATDD red scaffolds → dev-story → code-review) forced a spec, then failing tests, then implementation, then an independent review — each step catching what the previous missed. This produced far fewer defects than "write the feature."
- **Adversarial code review with 3 parallel independent reviewers** ("Blind Hunter" for defects, "Edge Case Hunter" for boundaries, "Acceptance Auditor" against the spec/ACs), each run *without prior conversation context*. Independent perspectives surfaced issues a single review missed (e.g. the untested validation-display path).
- **"Reuse map" prompting.** Each story doc listed exactly what already existed (routes, templates, fixtures) with an instruction to *extend, not recreate*. This prevented the classic AI failure of reinventing existing code.
- **Pinning a contract in the tests first.** ATDD scaffolds asserting the expected route/response shape gave the implementer an unambiguous target.

---

## 2. MCP Server Usage

**No MCP servers were used in Phase 3.** MCP tool endpoints were available in the environment (e.g. Atlassian, Slack, Google Drive, Notion), but none were relevant to a self-contained local build with no external issue tracker, chat, or doc store in the loop. All state lived in the repo (`_bmad-output/`, `sprint-status.yaml`, the code, and the test suite).

*If the assignment requires MCP usage, honest options to add it meaningfully:*
- An **Atlassian/Jira MCP** to sync `sprint-status.yaml` story states (backlog → in-progress → review → done) to real tickets.
- A **Slack MCP** to post code-review summaries / test results to a channel.
- A **filesystem or DB MCP** if the app grew to a managed database.

I chose not to bolt these on artificially — documenting the honest "not needed here, and why" is more accurate than a contrived integration.

---

## 3. Test Generation

**How AI assisted:**
- Generated a **test-design** (risk-scored scenarios per story, tagged by level unit/integration/e2e and priority P0–P2) before any code.
- Generated **ATDD red-phase scaffolds** — real assertions of expected behavior, kept skipped until each task was implemented (skip → RED → GREEN).
- Reused shared helpers (`TodoClient`, factories, `assert_single_item_fragment`, DB seeding) instead of duplicating fixtures.
- Verified scaffolds were **genuinely red** before implementing (activated them against the current/empty app and confirmed they failed for the right reason).

**What AI missed (caught later, documented honestly):**
- **Over-constrained assertion (1.1-UNIT-002):** the generated test asserted `created_at.tzinfo is not None`, but **SQLite stores datetimes naive** — the assertion could never pass on this stack. Caught by running the activated test against a correct stub; fixed to verify UTC by value proximity.
- **A real bug the integration tests could NOT catch (1.2):** the tests always sent the `description` field, but a **browser omits an empty input**, so `description` arrived *missing* and hit FastAPI's own JSON 422 before our validation. Green integration suite, broken UX. Caught only by driving a real browser. Fix: `Form("")` + a regression test that posts with no field.
- **Coverage gaps flagged in review:** AC "reflected on reload" (1.3) and "no full page reload" (1.4) were only implied, never asserted; the delete happy-path never proved *other* rows survived. All added as patches during code review.
- **Client-side behavior blind spot:** integration tests assert the server response, not that HTMX actually swaps it into the DOM — so the entire validation-*display* mechanism was initially untested.

Takeaway: AI generates thorough *server-contract* tests quickly, but tends to under-test **client/browser behavior** and can encode **stack-specific false assumptions** (the SQLite tz case). Both were caught by an explicit "run the real thing" step.

---

## 4. Debugging with AI

**Case A — HTMX won't show the 422 validation message (Story 1.2).**
Symptom: server correctly returned `422 + _error.html`, but the browser showed nothing.
AI debugging path (instrumented the real browser with Playwright):
1. Confirmed server response was correct (curl showed 422 + headers + fragment).
2. Instrumented `htmx:beforeSwap` in-page → found `shouldSwap:false` — htmx ignores non-2xx swaps by default.
3. Tried the `response-targets` extension → still `shouldSwap:false`; discovered its `responseTargetPrefersRetargetHeader` default made it *defer* to a server header I was also sending (they conflicted).
4. Replaced it with a small, understood inline `htmx:beforeSwap` handler and removed the extension.
5. Re-ran → the FastAPI JSON 422 appeared in the error slot, which exposed the *separate* `Form("")` missing-field bug (Case in §3).

**Case B — config guard bypasses (Story 1.1 review).**
AI enumerated inputs that defeated the `:memory:` guard (`mode=memory` URI form, `:MEMORY:` case, whitespace, non-SQLite scheme) and confirmed each with a quick harness script, then hardened the guard.

Pattern that worked: **make the failure observable** (instrument the browser / write a probe script) rather than reasoning about it abstractly.

---

## 5. Limitations Encountered / Where Human Expertise Was Critical

- **"Green tests" is not "it works."** The single most important lesson: the integration suite was green while the validation UX was broken in a real browser. **Insisting on end-to-end verification in the actual runtime** (live uvicorn + Playwright/curl) — not just passing tests — caught bugs the suite structurally could not. This judgment call is human-driven.
- **Framework-version quirks need empirical iteration.** The HTMX 2.x + `response-targets` incompatibility wasn't in the model's "knowledge"; it took hypothesis → browser instrumentation → observation → revision. AI is good at running that loop *if told to verify empirically*, but won't discover such quirks by reasoning alone.
- **Independent review is weaker when the reviewer is the author.** Code review here was run by the same model that wrote the code. It still found real issues (via the adversarial multi-agent structure), but a genuinely different reviewer/LLM would be more trustworthy — a known limitation I flagged each time.
- **Architecture judgment.** The containerization task template assumed "frontend + backend + database" containers; the real architecture is a single hypermedia monolith with embedded SQLite. Blindly following the template would have produced a wrong (frontend/DB) setup. **Recognizing the mismatch and adapting to one image + a volume was a design decision**, not a mechanical step.
- **Scope discipline.** AI will happily "improve" beyond scope. Human-set boundaries (defer error-UX to Epic 2, no auth in v1, no length cap until decided) kept the work aligned with the PRD; several review findings were correctly *deferred* rather than fixed.
- **Product decisions aren't AI's to make.** e.g. the max-description-length cap was surfaced as a decision (PRD had it as an open question) and required a human choice (500 chars), not an AI default.

---

## Appendix — Traceability

- Per-story detail: `_bmad-output/implementation-artifacts/1-*.md` (Dev Agent Record, Review Findings, Change Log).
- Test design + ATDD checklists: `_bmad-output/test-artifacts/`.
- Deferred backlog (with rationale): `_bmad-output/implementation-artifacts/deferred-work.md`.
- Sprint state: `_bmad-output/implementation-artifacts/sprint-status.yaml`.
