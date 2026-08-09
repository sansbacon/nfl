.PHONY: install install-dev test test-all lint format clean

# Install core library only (no Databricks deps)
install:
	pip install -e .

# Install core + Databricks extensions (full dev environment)
install-dev:
	pip install -e ".[dev,iceberg]" -e "packages/nfl-databricks[dev]"

# Run core library tests only
test:
	pytest tests/ -m "not integration"

# Run all tests (core + nfl-databricks)
test-all:
	pytest tests/ packages/nfl-databricks/tests/ -m "not integration"

# Run integration tests (requires Databricks runtime)
test-integration:
	pytest tests/ packages/nfl-databricks/tests/ -m "integration"

# Lint both packages
lint:
	ruff check src/ packages/nfl-databricks/src/ tests/ packages/nfl-databricks/tests/

# Format both packages
format:
	ruff format src/ packages/nfl-databricks/src/ tests/ packages/nfl-databricks/tests/

# Type check
typecheck:
	mypy src/ packages/nfl-databricks/src/

# Clean build artifacts
clean:
	rm -rf build/ dist/ src/*.egg-info packages/nfl-databricks/build/ packages/nfl-databricks/dist/ packages/nfl-databricks/src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
