# Addendum — Todo App

Downstream depth that informs architecture/UX but does not belong in the PRD's requirement narrative.

## Technical direction (for Architecture, not requirements)
- **Full-stack** split: responsive web frontend + small backend API. The PRD deliberately states capabilities (durable CRUD) rather than the storage engine or framework.
- **Language/runtime:** project is scaffolded as `nearform_python` with a `venv` present — a Python backend is the likely intent. `[ASSUMPTION — confirm with Architecture step; not fixed in the PRD.]`
- **Persistence:** FR-9 requires durability across restarts. Options range from a single-file store (e.g., SQLite/JSON) to a full database. Choice deferred to Architecture; simplicity favored given hobby stakes.

## Extensibility notes (why v1 is shaped this way)
- v1 excludes auth/multi-user, but the data model and API should not hard-code a single-user assumption in a way that blocks adding an owner/user relationship later.
- Deferred capabilities (priorities, deadlines, notifications, editing) were named as explicit non-goals to keep the epics/stories tight, not because they are technically hard.

## Qualitative intent to preserve
- "Feels like a complete, usable product despite minimal scope" — polish (empty/loading/error states, instant feedback, clear completed styling) is load-bearing, not optional garnish.
- Restraint is a design value: resist scope creep (see counter-metric SM-C1).
