# Deferred Work

## Deferred from: code review of 1-1-see-my-todo-list-when-i-open-the-app (2026-07-17)

- **[low] `created_at` UTC not truly guaranteed on SQLite** [app/models.py:33] — SQLite drops tz-awareness; `created_at` reads back naive and the unit test only checks value-proximity, not UTC. A real UTC guarantee needs a SQLAlchemy `TypeDecorator` (normalize on write/read). Over-engineering for v1 per the spine; revisit if non-UTC writes ever appear.
- **[low] Read-path error handling / wire `_error.html`** [app/routes/todos.py:21, app/templates/_error.html] — the list route has no try/except and the seeded error fragment is unwired. AD-5 (uniform error crossing) and FR-7 (empty/loading/error states) are Epic 2 scope; `_error.html` was intentionally seeded now for reuse.
- **[low] No pagination on the todo list** [app/routes/todos.py:25] — `GET /` materialises and renders the full table each request. PERF risk R8 is monitor-only at personal scale (test-design); add a limit/pagination if list sizes grow.
- **[low] SQLite concurrency hardening** [app/db.py:53] — `check_same_thread=False` is set but there is no WAL pragma / busy-timeout / `pool_pre_ping`. Harmless for 1.1's read-only path; add before/with the write routes (Story 1.2+) to avoid `database is locked`. — ✅ RESOLVED in Story 1.2 (WAL + busy_timeout connect event).

## Deferred from: code review of 1-2-add-a-new-todo (2026-07-17)

- **[low] Silent 500 on write failure** [app/routes/todos.py:56] — if `session.commit()` raises (disk full, lock past busy_timeout, integrity error), a bare 500 propagates and the inline `htmx:beforeSwap` handler (which only forces swap for 422) discards it, so the user sees nothing. General error-state UX (non-disruptive error fragment for any failure) is Epic 2 scope (FR-7 / AD-5). Consider a broader error handler + a global htmx error display there.
- **[low] No CSRF/origin protection on `POST /todos`** — v1 has no auth/session so there is no forgeable surface, but when accounts/auth are added (AD-6 anticipates this) the mutation routes need CSRF tokens or SameSite/origin checks.
- **[low] Double-submit duplicates** — fast double-click/Enter commits two identical rows; no button-disable or dedup. Duplicates are permitted in v1, so this is minor UX polish (disable-on-submit) for Epic 2.

## Deferred from: code review of 1-3-mark-a-todo-complete-or-active-again (2026-07-17)

- **[med] Mutation-error UI display (toggle/delete)** — htmx ignores non-2xx swaps and the `beforeSwap` handler is scoped to `#add-form`, so a toggle/delete 404 is fetched and discarded; in a stale tab the checkbox is left visually flipped with no message. Epic 2 (FR-7/AD-5) owns non-disruptive mutation-error display. **AD-7 constraint for the fix:** route the error fragment to a dedicated error region — do NOT swap it into `#todo-{id}` with `outerHTML` (that replaces/destroys the item row). Consider reverting the optimistic checkbox state on error.
- **[low] Toggle lost-update under concurrency** — `todo.completed = not todo.completed` is an unguarded read-modify-write; two interleaved toggles net a single flip. Fine for v1 personal single-user scale; add a row lock / version column / set-to-target semantics when multi-user/auth lands (AD-6). Also relates to the spine's "toggling is idempotent per target state" convention — a set-to-submitted-state design would satisfy both.

## Deferred from: code review of 1-4-delete-a-todo (2026-07-17)

- **[med] Mutation-error UI for delete** — same as toggle: a delete 404 (`_error.html`) is not shown in the browser (htmx ignores non-2xx; `beforeSwap` scoped to `#add-form`). Epic 2 (FR-7/AD-5). AD-7 constraint: route the error to a dedicated region, never `#todo-{id}` outerHTML.
- **[med] Delete/toggle concurrency** — a toggle that loaded a row before a concurrent delete commits will UPDATE 0 rows yet return a rendered fragment (phantom row re-inserted in the DOM); two concurrent deletes can raise `StaleDataError` → 500. Personal-scale single-user makes this rare in v1; address with row locks / affected-row checks / set-to-target when multi-user/auth lands (AD-6).
- **[low] No confirm/undo on delete** — a single click hard-deletes with no confirmation or undo (accidental data loss). Documented v1 decision (kept the journey E2E simple); add `hx-confirm` and/or a soft-delete+undo affordance in Epic 2.
- **[low] Empty-list state** — deleting the last todo leaves a bare empty `<ul id="todo-list">`. Epic 2 Story 2.2 (FR-7 empty state) owns the friendly placeholder.
