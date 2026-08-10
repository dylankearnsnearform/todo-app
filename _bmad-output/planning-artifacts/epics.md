---
stepsCompleted: [step-01-validate-prerequisites, step-02-design-epics, step-03-create-stories]
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-nearform_python-2026-07-14/prd.md
  - _bmad-output/planning-artifacts/architecture/architecture-nearform_python-2026-07-14/ARCHITECTURE-SPINE.md
---

# Todo App - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for the Todo App, decomposing the requirements from the PRD and Architecture spine into implementable stories. No dedicated UX design contract exists; UI requirements are carried by the PRD (FR-6, FR-7) and the architecture spine.

## Requirements Inventory

### Functional Requirements

FR-1: The User can create a Todo by entering a non-empty description; it appears in the list without a manual refresh, with completion status = active and a created-at timestamp. Empty/whitespace descriptions are rejected.
FR-2: The User sees their Todo list immediately on opening the app (no login/onboarding); all persisted Todos are fetched, active and completed both shown, newest-first, stable across reloads.
FR-3: The User can toggle a Todo's completion status (complete ↔ active); the change persists and completed Todos are visually distinct.
FR-4: The User can permanently delete a Todo; it is removed from the list and storage and does not reappear after reload.
FR-5: The interface reflects add/complete/delete actions immediately (well under a second); on backend rejection the UI reconciles to true state and informs the User.
FR-6: The layout adapts to desktop and mobile viewports without horizontal scrolling; completion status is legible at a glance.
FR-7: The app shows sensible empty, loading, and error states; failures are non-disruptive and the app stays usable.
FR-8: The backend exposes CRUD endpoints (create, list, toggle-completion, delete) with consistent, machine-readable/renderable responses.
FR-9: Todo data is durable and consistent — it survives server restarts and is served identically across sessions/devices (single shared store).

### NonFunctional Requirements

NFR-1: Simplicity & maintainability — the solution must be easy to understand, deploy, and extend by future developers.
NFR-2: Performance — interactions feel instantaneous under normal conditions (visible result well under a second).
NFR-3: Robust error handling — graceful client-side and server-side handling; malformed/failing requests return a clear error status without crashing the service.
NFR-4: Extensibility — the architecture must not preclude adding accounts/auth/multi-user later (no single-user assumption hard-coded).

### Additional Requirements

*(from the Architecture spine — binding invariants and stack)*

- **Project scaffold (Epic 1, Story 1):** No named third-party starter; the spine defines the greenfield source tree to scaffold — a single FastAPI app (`app/main.py`, `app/routes/`, `app/models.py`, `app/db.py`, `app/templates/`, `app/static/`, `tests/`, `pyproject.toml`).
- **Stack (verified 2026-07-14):** Python 3.12+, FastAPI 0.139.x, Uvicorn, Jinja2, HTMX 2.x, SQLAlchemy 2.0.x, SQLite.
- **AD-1 — Hypermedia monolith:** user actions are HTMX requests returning HTML (page or fragment); no client-side framework or JSON-only UI.
- **AD-2 — One deployable process:** a single FastAPI process serves HTML routes and mutations; no separate frontend server.
- **AD-3 — SQLite single source of truth:** backend is sole writer; client caches nothing authoritative.
- **AD-4 — Mutations via route handlers:** every create/toggle/delete goes route → DB write → updated HTML fragment; templates never touch the DB.
- **AD-5 — Uniform error crossing:** failed request returns proper HTTP status **and** a rendered error fragment.
- **AD-6 — No single-user assumption:** Todo store and queries must accept an owner/user relationship being added later without restructuring.
- **AD-7 — Fixed hypermedia swap contract:** list container id `#todo-list`; each item fragment single root element id `todo-<id>`; consistent `hx-target`/`hx-swap`.
- **Conventions:** integer PK per Todo; `created_at` stored UTC (ISO 8601); boolean `completed`, toggle idempotent per target state; config/DB path from environment, not scattered literals.

### UX Design Requirements

N/A — no dedicated UX design contract was produced. UI requirements are covered by FR-6 (responsive/legible), FR-7 (empty/loading/error states), and AD-1/AD-5/AD-7.

### FR Coverage Map

FR-1: Epic 1 - Create a Todo (HTMX form → route → DB → fragment)
FR-2: Epic 1 - View the Todo list on load
FR-3: Epic 1 - Toggle completion status
FR-4: Epic 1 - Delete a Todo
FR-5: Epic 1 - Instant feedback via HTMX fragment swaps (intrinsic to CRUD)
FR-6: Epic 2 - Responsive, legible layout
FR-7: Epic 2 - Empty, loading, and error states
FR-8: Epic 1 - CRUD API for Todos
FR-9: Epic 1 - Durable, consistent SQLite persistence

## Epic List

### Epic 1: A Working Todo App
A user can create, view, complete, and delete tasks, with changes reflected instantly and saved durably across restarts. Delivers the complete, usable core of the product. Includes the initial FastAPI app scaffold per the architecture spine's source tree.
**FRs covered:** FR-1, FR-2, FR-3, FR-4, FR-5, FR-8, FR-9

### Epic 2: A Polished, Responsive Experience
The app feels complete on any device — a responsive layout plus sensible empty, loading, and error states. Builds on Epic 1's working core and delivers the "finished product" quality bar.
**FRs covered:** FR-6, FR-7

## Epic 1: A Working Todo App

A user can create, view, complete, and delete tasks, with changes reflected instantly and saved durably across restarts. Includes the initial FastAPI app scaffold per the architecture spine. (FR-1, FR-2, FR-3, FR-4, FR-5, FR-8, FR-9; governed by AD-1..AD-7.)

### Story 1.1: See my todo list when I open the app

As a user,
I want to open the app and immediately see my list of todos (persisted across restarts),
So that I have a reliable home for my tasks with no login or setup.

**Acceptance Criteria:**

**Given** a fresh checkout of the project
**When** the FastAPI app is scaffolded per the spine's source tree and started with uvicorn
**Then** the app serves an `index.html` page at `/` with no login or onboarding
**And** the page contains a list container with id `#todo-list` (per AD-7).

**Given** the app is running with a SQLite store (SQLAlchemy 2.0 `Todo` model: integer PK, `description`, `completed` boolean, `created_at` UTC)
**When** the page loads
**Then** all persisted Todos are fetched and rendered newest-first
**And** both active and completed Todos are shown.

**Given** one or more Todos exist
**When** the server process is stopped and restarted
**Then** the same Todos are still present on next load (FR-9).

**Given** the persistence layer is written
**When** the schema and queries are defined
**Then** no single-user assumption is hard-coded — an owner/user relationship can be added later without restructuring (AD-6).

### Story 1.2: Add a new todo

As a user,
I want to type a task description and add it to my list,
So that I can capture something before I forget it.

**Acceptance Criteria:**

**Given** the app is open
**When** I submit a non-empty description via the add form (HTMX request to a create route)
**Then** the route persists a new Todo (status active, `created_at` set) and returns its item fragment
**And** the new Todo appears in `#todo-list` instantly without a full-page reload (FR-5), as a single root element with id `todo-<id>` (AD-7).

**Given** the add form
**When** I submit an empty or whitespace-only description
**Then** no Todo is created
**And** a gentle validation message is shown.

**Given** a Todo was just created
**When** I reload the page
**Then** the created Todo is still present (persisted via AD-3/AD-4).

### Story 1.3: Mark a todo complete or active again

As a user,
I want to toggle a task between done and not-done,
So that I can track progress and correct mistakes.

**Acceptance Criteria:**

**Given** an active Todo in the list
**When** I toggle it (HTMX request to a toggle route)
**Then** its `completed` status flips and is persisted
**And** its item fragment is swapped in place instantly (FR-5), showing a completed Todo as visually distinct from an active one.

**Given** a completed Todo
**When** I toggle it again
**Then** it returns to active and persists (toggle is reversible and idempotent per target state).

**Given** a toggled Todo
**When** I reload the page
**Then** the persisted status is reflected.

### Story 1.4: Delete a todo

As a user,
I want to permanently remove a task,
So that I can clear out things I no longer care about.

**Acceptance Criteria:**

**Given** a Todo in the list
**When** I delete it (HTMX request to a delete route)
**Then** it is removed from the store and its element is removed from `#todo-list` instantly (FR-5).

**Given** a Todo was deleted
**When** I reload the page
**Then** the deleted Todo does not reappear.

## Epic 2: A Polished, Responsive Experience

The app feels complete on any device — a responsive layout plus sensible empty, loading, and error states. (FR-6, FR-7; governed by AD-5.)

### Story 2.1: Use the app comfortably on mobile and desktop

As a user,
I want a layout that adapts to my phone or laptop and clearly shows task status,
So that the app is comfortable to use anywhere.

**Acceptance Criteria:**

**Given** the app on a narrow mobile viewport
**When** I view and interact with the list
**Then** it is fully usable with no horizontal scrolling.

**Given** the app on a wide desktop viewport
**When** I view the list
**Then** the layout adapts sensibly (readable line lengths, appropriately sized controls).

**Given** a mix of active and completed Todos
**When** I scan the list
**Then** completion status is legible at a glance (e.g. strikethrough/dimmed for completed).

### Story 2.2: Get clear empty, loading, and error feedback

As a user,
I want the app to tell me when there's nothing to show, when it's working, and when something failed,
So that I'm never staring at a blank or broken screen.

**Acceptance Criteria:**

**Given** I have no Todos
**When** the list loads
**Then** a friendly empty state is shown that invites me to add my first task.

**Given** the list or an action is in flight
**When** the request has not yet returned
**Then** a loading indication is shown rather than a blank/broken screen.

**Given** a fetch or action fails
**When** the server returns an error status
**Then** a non-disruptive error message is shown via a rendered error fragment (AD-5)
**And** the app remains usable (the UI reconciles to true state rather than crashing).
