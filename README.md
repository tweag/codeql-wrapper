# CodeQL Wrapper

[![Tests](https://github.com/ModusCreate-Perdigao-GHAS-Playground/codeql-wrapper/actions/workflows/test.yml/badge.svg)](https://github.com/ModusCreate-Perdigao-GHAS-Playground/codeql-wrapper/actions/workflows/test.yml)
[![Lint](https://github.com/ModusCreate-Perdigao-GHAS-Playground/codeql-wrapper/actions/workflows/lint.yml/badge.svg)](https://github.com/ModusCreate-Perdigao-GHAS-Playground/codeql-wrapper/actions/workflows/lint.yml)
[![Build](https://github.com/ModusCreate-Perdigao-GHAS-Playground/codeql-wrapper/actions/workflows/build.yml/badge.svg)](https://github.com/ModusCreate-Perdigao-GHAS-Playground/codeql-wrapper/actions/workflows/build.yml)
[![PyPI version](https://badge.fury.io/py/codeql-wrapper.svg)](https://badge.fury.io/py/codeql-wrapper)
[![Python versions](https://img.shields.io/pypi/pyversions/codeql-wrapper.svg)](https://pypi.org/project/codeql-wrapper/)

A universal Python CLI wrapper for running CodeQL analysis on any type of project (monorepo or single repository) across different CI/CD platforms including Jenkins, GitHub Actions, Harness, and any environment where Python scripts can be executed.

## Features

- **Monorepo Support**: Automatically detect and analyze multiple projects within monorepos
- **Multi-Platform CI/CD**: Works seamlessly with Jenkins, GitHub Actions, Harness, and other CI/CD tools
- **Smart Project Detection**: Automatically identifies project types and languages
- **Parallel Processing**: Run analysis on multiple projects concurrently

## Installation

### From PyPI (when published)

```bash
pip install codeql-wrapper
```

### From Source

```bash
git clone https://github.com/ModusCreate-Perdigao-GHAS-Playground/codeql-wrapper.git
cd codeql-wrapper
poetry install
```

## Usage

### Command Line Interface

```bash
# Analyze a single repository
codeql-wrapper analyze /path/to/repository

# Analyze a monorepo (automatically detects sub-projects)
codeql-wrapper analyze /path/to/monorepo --monorepo

# Analyze specific languages only
codeql-wrapper analyze /path/to/repo --languages python,javascript

# Specify custom output directory
codeql-wrapper analyze /path/to/repo --output-dir /path/to/results

# Analyze as monorepo (detect sub-projects)
codeql-wrapper analyze /path/to/monorepo --monorepo

# Force CodeQL reinstallation before analysis
codeql-wrapper analyze /path/to/repo --force-install

# Run with verbose logging
codeql-wrapper analyze /path/to/repo --verbose

# Show available commands and options
codeql-wrapper --help
```

### CI/CD Integration Examples

#### GitHub Actions

```yaml
- name: Run CodeQL Analysis
  run: |
    pip install codeql-wrapper
    codeql-wrapper analyze $GITHUB_WORKSPACE --output-dir results
```

#### Jenkins

```groovy
stage('CodeQL Analysis') {
    steps {
        sh '''
            pip install codeql-wrapper
            codeql-wrapper analyze ${WORKSPACE} --monorepo --verbose
        '''
    }
}
```

#### Harness

```yaml
- step:
    type: Run
    name: CodeQL Analysis
    identifier: codeql_analysis
    spec:
      shell: Sh
      command: |
        pip install codeql-wrapper
        codeql-wrapper analyze /harness --languages java,python
```

## Development

### Prerequisites

- Python 3.8.1 or higher
- Poetry (install from https://python-poetry.org/docs/#installation)

### Setup Development Environment

```bash
# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Clone the repository
git clone https://github.com/ModusCreate-Perdigao-GHAS-Playground/codeql-wrapper.git
cd codeql-wrapper

# Install dependencies
poetry install
```

### Development Commands

```bash
# Run the CLI (shows help)
poetry run codeql-wrapper

# Analyze a sample project
poetry run codeql-wrapper analyze ./sample-project

# Run tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=src/codeql_wrapper --cov-report=term-missing

# Format code
poetry run black src/ tests/

# Type checking
poetry run mypy src/

# Linting
poetry run flake8 src/ tests/

# Run all quality checks
poetry run pytest && poetry run black src/ tests/ && poetry run mypy src/ && poetry run flake8 src/ tests/
```

### Building and Publishing

```bash
# Build the package
poetry build

# Publish to PyPI (requires authentication)
poetry config pypi-token.pypi <your-token>
poetry publish

# Or publish to test PyPI first
poetry config repositories.testpypi https://test.pypi.org/legacy/
poetry publish -r testpypi
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and quality checks (`poetry run pytest && poetry run black src/ tests/`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

#### Workflows:

- **`test.yml`**: Test across multiple Python versions and OS
- **`lint.yml`**: Code quality checks (black, flake8, mypy)
- **`build.yml`**: Package building and installation testing
- **`release.yml`**: Automated releases to PyPI when tags are pushed

## License

MIT License - see LICENSE file for details.
