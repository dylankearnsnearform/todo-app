"""Todo routes.

Story 1.1 delivers the read/list path: ``GET /`` renders the full page with the
persisted todos, newest-first, showing both active and completed (FR-2). Mutation
routes (create/toggle/delete) are added in stories 1.2–1.4 and will live here,
verb-scoped under ``/todos`` per the spine.
"""

from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select

from app import db as dbmod
from app.models import Todo, description_error
from app.templating import templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    """Render the todo list page. All persisted todos, newest-first (AD-3/AD-7)."""
    with dbmod.get_session() as session:
        todos = session.scalars(
            select(Todo).order_by(Todo.created_at.desc(), Todo.id.desc())
        ).all()
    return templates.TemplateResponse(request, "index.html", {"todos": todos})


@router.post("/todos", response_class=HTMLResponse)
def create(request: Request, description: str = Form("")) -> HTMLResponse:
    """Create a Todo from the add form and return its item fragment (AD-4/AD-7).

    Invalid (empty/whitespace) input returns a 422 + rendered error fragment
    (AD-5) and creates no row; a small htmx:beforeSwap handler in index.html shows
    it in the form's error slot.
    """
    error = description_error(description)
    if error is not None:
        # 422 + rendered error fragment (AD-5). A small htmx:beforeSwap handler
        # in index.html routes this to #add-error (htmx ignores non-2xx swaps by
        # default); HX-Reswap makes it a clean replace so errors don't stack.
        response = templates.TemplateResponse(
            request,
            "_error.html",
            {"message": error},
            status_code=422,
        )
        response.headers["HX-Reswap"] = "innerHTML"
        return response

    with dbmod.get_session() as session:
        todo = Todo(description=description.strip())
        session.add(todo)
        session.commit()  # explicit commit — every write path commits (AD-4)
        session.refresh(todo)
        return templates.TemplateResponse(request, "_todo_item.html", {"todo": todo})


@router.post("/todos/{todo_id}/toggle", response_class=HTMLResponse)
def toggle(request: Request, todo_id: int) -> HTMLResponse:
    """Flip a Todo's completion and return its updated item fragment (AD-4/AD-7).

    A missing id (stale tab / already-removed) returns a 404 + rendered error
    fragment (AD-5/R3), never an unhandled 500, and changes no row.
    """
    with dbmod.get_session() as session:
        todo = session.get(Todo, todo_id)
        if todo is None:
            return templates.TemplateResponse(
                request,
                "_error.html",
                {"message": "That todo no longer exists."},
                status_code=404,
            )
        todo.completed = not todo.completed
        session.commit()  # explicit commit (AD-4)
        # No refresh needed: expire_on_commit=False keeps the flipped value + id live.
        return templates.TemplateResponse(request, "_todo_item.html", {"todo": todo})


@router.delete("/todos/{todo_id}", response_class=HTMLResponse)
def delete(request: Request, todo_id: int) -> HTMLResponse:
    """Delete a Todo and return an empty 200 so the outerHTML swap removes its
    element (AD-4). A missing id returns 404 + rendered error fragment (AD-5/R3),
    never a 500, and changes no row.
    """
    with dbmod.get_session() as session:
        todo = session.get(Todo, todo_id)
        if todo is None:
            return templates.TemplateResponse(
                request,
                "_error.html",
                {"message": "That todo no longer exists."},
                status_code=404,
            )
        session.delete(todo)
        session.commit()  # explicit commit (AD-4)
        return HTMLResponse("", status_code=200)
