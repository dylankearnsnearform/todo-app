---
title: Todo App
status: final
created: 2026-07-14
updated: 2026-07-15
---

# PRD: Todo App

## 0. Document Purpose

This PRD is for the builder (Dylan) and any future contributor picking up the Todo App. It defines *what* v1 must do and why, so downstream architecture, epics, and implementation stay consistent. It is deliberately lean: a single feature area, functional requirements nested under grouped features, and a short glossary the rest of the document uses verbatim. Technology choices (language, framework, storage engine) are intentionally excluded here and captured in the sibling `addendum.md`. Inferences made without explicit confirmation are tagged `[ASSUMPTION]` inline and indexed in §9.

## 1. Vision

The Todo App is a simple, full-stack application for managing personal tasks with zero friction. A single user opens the app and immediately sees their list of todos — no login, no onboarding, no explanation. They can add a task, mark it done, and remove it, with the interface responding instantly to every action.

The product's value is its restraint. It does one thing — personal task management — and does it reliably across refreshes and sessions. Completed tasks are visually distinct from active ones so status is legible at a glance, and the app behaves gracefully when it has nothing to show or something goes wrong.

While v1 is intentionally minimal, the architecture should not foreclose later growth (accounts, multi-user, priorities, deadlines). The bar for v1 is that it feels like a complete, usable product despite its small scope.

## 2. Target User

### 2.1 Jobs To Be Done
- **Functional:** Capture a task quickly before I forget it.
- **Functional:** See everything I still need to do, at a glance.
- **Functional:** Mark a task done and get the satisfaction of it looking done.
- **Functional:** Clear out tasks I no longer care about.
- **Contextual:** Do all of the above on my phone or laptop, without signing in.
- **Builder's job:** Ship a clean, reliable full-stack app I can extend and learn from. `[ASSUMPTION: this is primarily a personal/learning build for a single operator.]`

### 2.2 Non-Users (v1)
- Teams needing shared or collaborative lists.
- Anyone requiring accounts, sync across identities, or access control.

### 2.3 Key User Journeys

- **UJ-1. Dylan clears his list on the go.** Dylan, mid-morning with a few things on his mind, opens the app on his phone (no login). He sees his current todos, types "Book dentist" and adds it — it appears instantly in the list. He taps an earlier task to mark it complete; it visibly styles as done. He deletes a stale task he no longer needs. He closes the app confident the changes are saved, and reopening later (or on his laptop) shows the same state.

## 3. Glossary

- **Todo** — A single personal task. Has a textual **description**, a **completion status** (active or completed), and creation metadata (**created-at** timestamp). The atomic unit of the app.
- **Description** — The short free-text label of a Todo.
- **Completion status** — Whether a Todo is *active* or *completed*. Toggleable.
- **Todo list** — The full, ordered collection of the User's Todos shown on opening the app.
- **User** — The single individual using the app. v1 has no concept of multiple distinct users.

## 4. Features

### 4.1 Task Management

**Description:** The core of the app. The User can create, view, complete/uncomplete, and delete Todos. Editing an existing Todo's description is not offered in v1 — to change a task, the User deletes it and creates a new one. Realizes UJ-1. `[ASSUMPTION: editing a Todo's text is out of scope for v1, in keeping with the deliberately minimal scope.]`

**Functional Requirements:**

#### FR-1: Create a Todo
The User can create a Todo by entering a description. Realizes UJ-1.

**Consequences (testable):**
- Submitting a non-empty description adds a new Todo with completion status = active and a created-at timestamp.
- The new Todo appears in the Todo list without a manual refresh.
- Submitting an empty/whitespace-only description does not create a Todo and surfaces a gentle validation message. `[ASSUMPTION: empty descriptions are rejected.]`

#### FR-2: View the Todo list
The User sees their Todo list immediately on opening the app, with no login or onboarding. Realizes UJ-1.

**Consequences (testable):**
- On load, all persisted Todos are fetched and displayed.
- Active and completed Todos are both shown. `[ASSUMPTION: completed items remain visible in the list rather than being hidden.]`
- Ordering is stable across reloads. `[ASSUMPTION: newest-first ordering by created-at.]`

#### FR-3: Toggle completion status
The User can mark a Todo complete, and mark a completed Todo active again. Realizes UJ-1.

**Consequences (testable):**
- Toggling a Todo updates its completion status and persists the change.
- A completed Todo is visually distinguishable from an active one (e.g., strikethrough/dimmed). `[ASSUMPTION: completion is a reversible toggle, not a one-way action.]`

#### FR-4: Delete a Todo
The User can permanently remove a Todo. Realizes UJ-1.

**Consequences (testable):**
- Deleting a Todo removes it from the list and from storage.
- A deleted Todo does not reappear after reload.

### 4.2 Interface & Feedback

**Description:** The interface is fast, responsive, and honest about state. It works across desktop and mobile browsers and reflects actions instantly. `[ASSUMPTION: v1 is a single responsive web app, not a native mobile or desktop app.]`

**Functional Requirements:**

#### FR-5: Instant feedback on actions
When the User adds, completes, or deletes a Todo, the interface reflects the change immediately rather than waiting on a perceptible round-trip. Realizes UJ-1.

**Consequences (testable):**
- Under normal conditions, the visible result of an action appears in well under a second.
- If the backend rejects an action, the UI reconciles to the true state and informs the User (see FR-7).

#### FR-6: Responsive, legible layout
The layout adapts to desktop and mobile viewports, and completion status is legible at a glance.

**Consequences (testable):**
- The list is usable on a narrow mobile viewport and a wide desktop viewport without horizontal scrolling.
- Completed Todos are clearly distinct from active Todos.

#### FR-7: Empty, loading, and error states
The app communicates when there is nothing to show, when it is working, and when something failed.

**Consequences (testable):**
- With no Todos, an empty state invites the User to add their first task.
- While fetching, a loading indication is shown rather than a blank/broken screen.
- On a failed action or fetch, a non-disruptive error message is shown and the app remains usable.

### 4.3 Persistence & API

**Description:** A small, well-defined backend API persists and retrieves Todo data with CRUD operations, ensuring durability and consistency across sessions.

**Functional Requirements:**

#### FR-8: CRUD API for Todos
The backend exposes endpoints to create, read, update (completion status), and delete Todos.

**Consequences (testable):**
- Each of create, list, toggle-completion, and delete is served by a defined endpoint.
- Responses are consistent and machine-readable, enabling the frontend to reconcile state.

#### FR-9: Durable, consistent persistence
Todo data survives server restarts and remains consistent across sessions and devices. `[ASSUMPTION: "durable across sessions" means data persists to durable storage (file or database), not in-memory only.]`

**Consequences (testable):**
- Todos created in one session are present after a server restart.
- The same data is served regardless of which browser/device fetches it (single shared store, single user).

**Feature-specific NFRs:**
- Basic server-side error handling: malformed or failing requests return a clear error status without crashing the service.

## 5. Non-Goals (Explicit)
- Not a multi-user or collaborative product — no shared lists.
- Not an account system — no authentication, authorization, or user profiles in v1.
- Not a full task manager — no priorities, deadlines, reminders, tags, or notifications.
- Not offline-first — v1 assumes connectivity to the backend.

## 6. MVP Scope

### 6.1 In Scope
- Create, view, toggle-complete, and delete Todos.
- Responsive web interface with instant feedback and empty/loading/error states.
- Backend CRUD API with durable persistence.

### 6.2 Out of Scope for MVP
- Editing a Todo's description (delete + recreate instead). `[NOTE FOR PM: cheap to add later; revisit if it annoys real use.]`
- User accounts, auth, and multi-user support — *architecture must not preclude adding these later.*
- Task prioritization, deadlines, notifications, collaboration.
- Offline support / local caching.

## 7. Success Metrics

**Primary**
- **SM-1**: A first-time User can complete all core actions (create, view, complete, delete) with no guidance or onboarding. Validates FR-1–FR-4, FR-7.

**Secondary**
- **SM-2**: Data survives refreshes, restarts, and re-opens with zero observed loss. Validates FR-9.
- **SM-3**: Actions feel instantaneous under normal conditions. Validates FR-5.

**Counter-metrics (do not optimize)**
- **SM-C1**: Feature count — resist adding capabilities just to seem complete. Counterbalances the pull to grow past the minimal core; the product's value is its restraint.

## 8. Open Questions
1. Should completed Todos eventually be hidden/collapsed, or is an always-visible list fine long term?
2. Is there any cap on the number of Todos or on description length worth enforcing?

## 9. Assumptions Index
- §2.1 — This is primarily a personal/learning build for a single operator.
- §4.1 — Editing a Todo's text is out of scope for v1.
- §4.1 (FR-1) — Empty/whitespace descriptions are rejected.
- §4.1 (FR-2) — Completed items remain visible in the list.
- §4.1 (FR-2) — Todo list is ordered newest-first by created-at.
- §4.1 (FR-3) — Completion is a reversible toggle.
- §4.2 — v1 is a single responsive web app (not native mobile/desktop).
- §4.3 (FR-9) — "Durable across sessions" means persistence to durable storage (file or database), not in-memory only.
