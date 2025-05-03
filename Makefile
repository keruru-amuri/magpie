.PHONY: help test test-cov test-unit test-integration lint format clean

# Default target
help:
	@echo "Available commands:"
	@echo "  make test              Run all tests"
	@echo "  make test-cov          Run tests with coverage report"
	@echo "  make test-unit         Run unit tests only"
	@echo "  make test-integration  Run integration tests only"
	@echo "  make lint              Run linting checks"
	@echo "  make format            Format code with black and isort"
	@echo "  make clean             Clean up cache and temporary files"

# Run all tests
test:
	pytest

# Run tests with coverage report
test-cov:
	pytest --cov=app --cov-report=term-missing --cov-report=html:coverage_html

# Run unit tests only
test-unit:
	pytest tests/unit

# Run integration tests only
test-integration:
	pytest tests/integration

# Run linting checks
lint:
	flake8 app tests
	mypy app tests
	black --check app tests
	isort --check-only app tests

# Format code with black and isort
format:
	black app tests
	isort app tests

# Clean up cache and temporary files
clean:
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf coverage_html
	rm -rf .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name *.egg-info -exec rm -rf {} +
	find . -type f -name *.pyc -delete
