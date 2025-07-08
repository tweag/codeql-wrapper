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
- **SARIF Upload**: Built-in integration with GitHub Code Scanning using CodeQL's native upload functionality

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

# Analyze and upload SARIF results to GitHub Code Scanning
codeql-wrapper analyze /path/to/repo \
  --upload-sarif \
  --repository owner/repository \
  --commit-sha $COMMIT_SHA \
  --ref refs/heads/main

# Show available commands and options
codeql-wrapper --help
```

### SARIF Upload to GitHub Code Scanning

The wrapper provides built-in functionality to upload SARIF files to GitHub Code Scanning after analysis. It can automatically detect Git information (repository, commit SHA, and reference) when you're working in a Git repository with a GitHub remote.

```bash
# Upload a single SARIF file (auto-detects Git info)
codeql-wrapper upload-sarif /path/to/results.sarif

# Upload with explicit parameters
codeql-wrapper upload-sarif /path/to/results.sarif \
  --repository owner/repository \
  --commit-sha $COMMIT_SHA \
  --ref refs/heads/main \
  --github-token $GITHUB_TOKEN
```

#### Authentication

Set up authentication using one of these methods:

1. **Environment variable** (recommended for CI/CD):
   ```bash
   export GITHUB_TOKEN="your_github_token"
   codeql-wrapper upload-sarif results.sarif  # Auto-detects Git info
   ```

2. **Command line argument**:
   ```bash
   codeql-wrapper upload-sarif results.sarif --github-token "your_token"
   ```

The tool will automatically detect:
- **Repository**: From Git remote origin URL (if it's a GitHub repository)
- **Commit SHA**: From current Git HEAD
- **Reference**: From current Git branch or tag

You can override any auto-detected value by providing the corresponding command-line option.

The token requires the `security_events` scope for public repositories or `security_events` and `repo` scopes for private repositories.

#### Combined Analysis and Upload

```bash
# Analyze and upload in one command (auto-detects Git info)
codeql-wrapper analyze /path/to/repo --upload-sarif

# Analyze and upload with explicit parameters
codeql-wrapper analyze /path/to/repo \
  --upload-sarif \
  --repository owner/repository \
  --commit-sha $COMMIT_SHA \
  --ref $GITHUB_REF
```

### CI/CD Integration Examples

#### GitHub Actions

```yaml
- name: Run CodeQL Analysis and Upload Results
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  run: |
    pip install codeql-wrapper
    codeql-wrapper analyze $GITHUB_WORKSPACE \
      --upload-sarif \
      --repository ${{ github.repository }} \
      --commit-sha ${{ github.sha }} \
      --ref ${{ github.ref }}
```

#### Jenkins

```groovy
stage('CodeQL Analysis') {
    environment {
        GITHUB_TOKEN = credentials('github-token')
    }
    steps {
        sh '''
            pip install codeql-wrapper
            codeql-wrapper analyze ${WORKSPACE} \
              --monorepo --verbose \
              --upload-sarif \
              --repository owner/repository \
              --commit-sha ${GIT_COMMIT} \
              --ref ${GIT_BRANCH}
        '''
    }
}
```

#### Harness

```yaml
- step:
    type: Run
    name: CodeQL Analysis and Upload
    identifier: codeql_analysis
    spec:
      shell: Sh
      envVariables:
        GITHUB_TOKEN: <+secrets.getValue("github_token")>
      command: |
        pip install codeql-wrapper
        codeql-wrapper analyze /harness \
          --languages java,python \
          --upload-sarif \
          --repository owner/repository \
          --commit-sha ${DRONE_COMMIT_SHA} \
          --ref refs/heads/main
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

python3 -m venv .venv

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
