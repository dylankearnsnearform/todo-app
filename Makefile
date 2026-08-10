.PHONY: install install-browsers test test-unit test-integration test-api test-e2e test-cov clean

# One-time setup: install the app + test deps, then the Playwright browsers.
install:
	pip install -e ".[test]"

install-browsers:
	python -m playwright install --with-deps chromium

# Default test run: everything except the slow browser E2E tests.
test:
	pytest

test-unit:
	pytest -m unit

test-integration:
	pytest -m integration

test-api:
	pytest -m api

# Browser E2E. Boots a live server automatically (see tests/e2e/conftest.py).
# Trace/video/screenshot are retained only on failure for fast local runs.
test-e2e:
	pytest -m e2e --tracing=retain-on-failure --video=retain-on-failure --screenshot=only-on-failure

# Coverage over the in-process (unit + integration + api) suite.
test-cov:
	pytest -m "not e2e" --cov=app --cov-report=term-missing --cov-report=xml

clean:
	rm -rf .pytest_cache htmlcov test-results playwright-report .coverage coverage.xml
	find . -type d -name __pycache__ -not -path "./venv/*" -exec rm -rf {} +
