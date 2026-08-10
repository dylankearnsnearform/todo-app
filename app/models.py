"""Domain model: the Todo entity (SQLAlchemy 2.0).

Conventions (architecture spine): integer PK, `created_at` stored UTC, boolean
`completed`. No single-user assumption is hard-coded (AD-6) — a nullable owner
relationship can be added later without restructuring this table.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


#: Max length of a Todo description (product decision — guards R5 "oversized").
MAX_DESCRIPTION_LENGTH = 500


def is_valid_description(raw: str | None) -> bool:
    """A description is valid iff it is non-empty after trimming (FR-1)."""
    return bool(raw and raw.strip())


def description_error(raw: str | None) -> str | None:
    """Return a gentle validation message for a description, or None if valid.

    Rejects empty/whitespace (FR-1) and over-length input (R5 "oversized").
    """
    if not is_valid_description(raw):
        return "Please enter a description."
    if len(raw.strip()) > MAX_DESCRIPTION_LENGTH:
        return f"Description must be {MAX_DESCRIPTION_LENGTH} characters or fewer."
    return None


class Todo(Base):
    __tablename__ = "todos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    description: Mapped[str] = mapped_column(String, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"Todo(id={self.id!r}, completed={self.completed!r}, description={self.description!r})"
