# Todo App

A small, full-stack personal task manager: create, view, complete/uncomplete, and
delete todos, with changes reflected instantly and saved durably across restarts.

**Architecture:** a server-rendered **hypermedia monolith** — a single FastAPI
process renders HTML and HTMX issues requests that swap in HTML fragments. No JSON
SPA, no separate frontend build, no separate database server. State lives in a
SQLite file.

**Stack:** Python 3.12+ · FastAPI · Jinja2 · HTMX 2.x · SQLAlchemy 2.0 · SQLite.

---

## Quick start (local)

```bash
python -m venv venv && source venv/bin/activate
pip install -e ".[test]"          # app + test dependencies
uvicorn app.main:app --reload     # → http://localhost:8000
```

The database is created on startup. By default it lives at `./todo.db`
(override with `DATABASE_URL`, e.g. `sqlite:///./mydata.db`). In-memory SQLite is
rejected on purpose so data can't silently vanish on restart.

## Run with Docker

```bash
docker compose up --build          # → http://localhost:8000
docker compose logs -f app         # follow logs
docker compose down                # stop (data persists in the `todo-data` volume)
```

- One image (the monolith); SQLite persists in the named **`todo-data`** volume.
- Runs as a **non-root** user with a container **health check** on `/health`.
- Configure via env vars / `.env` (see `.env.example`): `PORT`, `DATABASE_URL`.

## Tests

```bash
make test          # unit + integration + api (fast, no browser)
make test-e2e      # Playwright end-to-end (boots a live server; needs browsers)
make test-cov      # coverage over the in-process suite

# one-time, for E2E:
python -m playwright install --with-deps chromium
```

Run the in-container test suite (unit/integration/api):

```bash
docker compose run --rm test
```

**Status:** 32 unit/integration/api tests + 6 Playwright E2E; ~96% app coverage;
E2E includes an axe-core accessibility scan asserting **zero critical WCAG
violations**.

## Layout

```
app/
  main.py            # FastAPI app factory + lifespan (schema init) + static mount
  db.py              # engine/session, DATABASE_URL resolution + guards, WAL pragma
  models.py          # Todo (SQLAlchemy 2.0) + description validation
  routes/
    todos.py         # GET / (list), POST /todos, POST /todos/{id}/toggle, DELETE /todos/{id}
    health.py        # GET /health (readiness/liveness)
  templating.py      # shared autoescaped Jinja2 environment
  templates/         # index.html, _todo_item.html, _error.html
  static/            # app.css, vendored htmx.min.js
tests/               # unit / integration / api / e2e + shared support helpers
Dockerfile           # multi-stage (builder → runtime), non-root, HEALTHCHECK
docker-compose.yml   # app service + todo-data volume + test profile
```

## HTTP surface

| Method & path | Purpose | Response |
| --- | --- | --- |
| `GET /` | The todo list page | full HTML page |
| `POST /todos` | Create a todo (form `description`) | item fragment (200) / error fragment (422) |
| `POST /todos/{id}/toggle` | Toggle complete/active | item fragment (200) / error (404) |
| `DELETE /todos/{id}` | Delete a todo | empty (200) / error (404) |
| `GET /health` | Health check | `{"status":"ok"}` (200) / (503) |

## Documentation

- **AI integration log:** [`AI-INTEGRATION-LOG.md`](AI-INTEGRATION-LOG.md)
- **Test suite guide:** [`tests/README.md`](tests/README.md)
- **Planning artifacts** (PRD, architecture spine, epics, test design):
  `_bmad-output/planning-artifacts/` and `_bmad-output/test-artifacts/`
- **Per-story records & deferred backlog:** `_bmad-output/implementation-artifacts/`

## Scope (v1)

In scope: full CRUD, instant HTMX feedback, durable SQLite persistence, containerized
deployment. Out of scope (v1 non-goals): accounts/auth/multi-user, priorities/deadlines,
editing a todo's text, offline support. Responsive layout and richer empty/loading/error
states are planned for Epic 2.
