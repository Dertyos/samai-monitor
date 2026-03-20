.PHONY: test test-integration test-cov build deploy clean

VENV = .venv/bin
PYTHON = $(VENV)/python
PYTEST = $(VENV)/pytest

# Run unit tests only (no network, no AWS)
test:
	PYTHONPATH=backend/layers/shared/python:backend $(PYTEST) backend/tests -v -m "not integration" --tb=short

# Run integration tests (hits real SAMAI API)
test-integration:
	PYTHONPATH=backend/layers/shared/python:backend $(PYTEST) backend/tests -v -m "integration" --tb=short

# Run all tests with coverage
test-cov:
	PYTHONPATH=backend/layers/shared/python:backend $(PYTEST) backend/tests -v --cov=backend/layers/shared/python --cov=backend/functions --cov-report=term-missing --tb=short

# SAM build
build:
	sam build

# SAM deploy (guided first time, then uses samconfig.toml)
deploy:
	sam deploy

# SAM deploy first time
deploy-guided:
	sam deploy --guided

# Clean build artifacts
clean:
	rm -rf .aws-sam/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
