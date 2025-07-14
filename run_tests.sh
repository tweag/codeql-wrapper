#!/bin/bash

# Enable command echoing (debug mode)
set -x

# Format checking
echo "Running format checks..."
poetry run black --check src/ tests/

# Linting (assuming tests/ directory exists)
echo "Running lint checks..."
poetry run flake8 src/ tests/

# Type checking
echo "Running type checks..."
poetry run mypy src/codeql_wrapper/

# Testing with coverage
echo "Running tests with coverage..."
poetry run pytest -v --cov=src/codeql_wrapper --cov-report=xml --cov-report=term-missing tests/