# syntax=docker/dockerfile:1
#
# Single-image build for the Todo App — a server-rendered hypermedia monolith
# (FastAPI + Jinja2 + HTMX + SQLite). There is no separate frontend or database
# service: the app renders HTML itself, and SQLite is an embedded file persisted
# via a mounted volume (see docker-compose.yml).

# ---------- base: shared source + venv skeleton ----------
FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/venv/bin:$PATH"
WORKDIR /app
RUN python -m venv /opt/venv
# Dependency manifest + source (templates/static live inside the app package).
COPY pyproject.toml ./
COPY app ./app

# ---------- builder: install runtime deps only (no [test]) ----------
FROM base AS builder
RUN pip install .

# ---------- runtime: lean, non-root production image ----------
FROM python:3.12-slim AS runtime
ENV PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app \
    DATABASE_URL=sqlite:////data/todo.db \
    PORT=8000
# Non-root user + a writable data dir for the SQLite volume.
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /data && chown -R appuser:appuser /data
COPY --from=builder /opt/venv /opt/venv
WORKDIR /app
COPY app ./app
USER appuser
EXPOSE 8000
# Container-native health check (no curl in slim — use stdlib urllib).
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import os,urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:%s/health' % os.environ.get('PORT','8000'), timeout=2).status==200 else 1)"
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]

# ---------- test: image that runs the suite (unit+integration+api) ----------
# Includes the [test] extra; E2E (browser) is intentionally excluded here to keep
# the image lean — run `make test-e2e` on the host / a Playwright CI image.
FROM base AS test
RUN pip install ".[test]"
COPY tests ./tests
ENV PYTHONPATH=/app \
    TEST_ENV=local
CMD ["pytest", "-m", "not e2e", "-q"]
