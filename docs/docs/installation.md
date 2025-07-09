---
sidebar_position: 2
---

# Installation

This guide covers different ways to install CodeQL Wrapper.

## Prerequisites

- **Python 3.8.1 or higher**
- **Poetry** (for development installation)
- **Git** (for repository analysis)

## Install from PyPI

The easiest way to install CodeQL Wrapper is from PyPI:

```bash
pip install codeql-wrapper
```

### Verify Installation

After installation, verify that CodeQL Wrapper is working:

```bash
codeql-wrapper --version
```

## Install from Source

For development or to get the latest features:

### 1. Clone the Repository

```bash
git clone https://github.com/ModusCreate-Perdigao-GHAS-Playground/codeql-wrapper.git
cd codeql-wrapper
```

### 2. Install Poetry

If you don't have Poetry installed:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### 3. Install Dependencies

```bash
poetry install
```

### 4. Run CodeQL Wrapper

```bash
poetry run codeql-wrapper --help
```

## Development Setup

For contributing to the project:

### 1. Install Development Dependencies

```bash
poetry install --with dev
```

### 2. Run Tests

```bash
poetry run pytest
```

```
# Run tests with coverage
poetry run pytest --cov=src/codeql_wrapper --cov-report=term-missing
```

### 3. Run Quality Checks

```bash
# Format code
poetry run black src/ tests/

# Type checking
poetry run mypy src/

# Linting
poetry run flake8 src/ tests/

# All checks
poetry run pytest && poetry run black src/ tests/ && poetry run mypy src/ && poetry run flake8 src/ tests/
```

### 4. Building and Publishing

```bash
# Build the package
poetry build

# Publish to PyPI (requires authentication)
poetry config pypi-token.pypi <your-token>
poetry publish

# Or publish to test PyPI first
poetry config repositories.testpypi https://test.pypi.org/legacy/
poetry publish -r testpypi

# Or run the release workflow on Github
```


## Docker Installation

> **Note**: Docker installation is not supported on ARM-based Macs (Apple Silicon) since CodeQL CLI does not work properly through Docker on macOS ARM.

CodeQL Wrapper can also be run in a Docker container:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --no-dev

COPY . .

ENTRYPOINT ["poetry", "run", "codeql-wrapper"]
```

Build and run:

```bash
docker build -t codeql-wrapper .
docker run --rm -v /path/to/repo:/workspace codeql-wrapper analyze /workspace
```

## Troubleshooting

### Common Issues

#### Python Version Error
Make sure you have Python 3.8.1 or higher:

```bash
python --version
```

#### Poetry Not Found
Make sure Poetry is in your PATH after installation:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

#### Permission Errors
On some systems, you might need to use `pip3` instead of `pip`:

```bash
pip3 install codeql-wrapper
```

### Getting Help

If you encounter issues:

1. Check the [Issues page](https://github.com/ModusCreate-Perdigao-GHAS-Playground/codeql-wrapper/issues)
2. Create a new issue with details about your problem
3. Include your Python version, operating system, and error messages
