---
sidebar_position: 2
---

# Installation

This guide covers different ways to install CodeQL Wrapper and its requirements.

## Prerequisites

### System Requirements

- **Python 3.8.1 or higher** (tested with Python 3.12 and 3.13)
- **Git** (for repository analysis and cloning source code)
- **Internet connection** (for automatic CodeQL CLI download and installation)

### Platform Support

CodeQL Wrapper supports the following platforms:
- **Linux** (Ubuntu, CentOS, RHEL, etc.)
- **macOS** (Intel and Apple Silicon)
- **Windows** (10, 11, and Windows Server)

### Optional Requirements

- **Poetry** (only required for development installation)
- **GitHub Personal Access Token** (for SARIF upload to GitHub Code Scanning)

## Install from PyPI (Recommended)

The easiest way to install CodeQL Wrapper is from PyPI using pip:

```bash
pip install codeql-wrapper
```

For Python environments where you need to use `pip3`:

```bash
pip3 install codeql-wrapper
```

### Verify Installation

After installation, verify that CodeQL Wrapper is working correctly:

```bash
codeql-wrapper --version
```

You should see output similar to:
```
0.1.5
```

### Test Basic Functionality

Run a quick help command to ensure all dependencies are working:

```bash
codeql-wrapper --help
```

## Install from Source

For development, contributing, or getting the latest unreleased features:

### 1. Clone the Repository

```bash
git clone https://github.com/ModusCreate-Perdigao-GHAS-Playground/codeql-wrapper.git
cd codeql-wrapper
```

### 2. Install Poetry

Poetry is required for dependency management. If you don't have Poetry installed:

**Linux/macOS:**
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

**Windows PowerShell:**
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

**Alternative (using pip):**
```bash
pip install poetry
```

### 3. Install Dependencies

Install the project and its dependencies:

```bash
poetry install
```

This creates a virtual environment and installs all required dependencies.

### 4. Run CodeQL Wrapper

Test the installation by running:

```bash
poetry run codeql-wrapper --help
```

### 5. Activate Virtual Environment (Optional)

To use CodeQL Wrapper directly without the `poetry run` prefix:

```bash
poetry shell
codeql-wrapper --help
```

## Development Setup

For contributing to the project or advanced development:

### 1. Install Development Dependencies

```bash
poetry install --with dev
```

This installs additional tools for testing, linting, and code formatting.

### 2. Run Tests

Run the complete test suite:

```bash
poetry run pytest
```

Run tests with coverage reporting:

```bash
poetry run pytest --cov=src/codeql_wrapper --cov-report=term-missing
```

Run tests for specific platforms (the CI runs tests on Python 3.12 and 3.13):

```bash
# Ensure compatibility across Python versions
poetry env use python3.12
poetry install --with dev
poetry run pytest
```

### 3. Code Quality Checks

The project uses several tools to maintain code quality:

**Format code with Black:**
```bash
poetry run black src/ tests/
```

**Type checking with MyPy:**
```bash
poetry run mypy src/
```

**Linting with Flake8:**
```bash
poetry run flake8 src/ tests/
```

**Run all quality checks at once:**
```bash
poetry run pytest && poetry run black src/ tests/ && poetry run mypy src/ && poetry run flake8 src/ tests/
```

### 4. Building and Publishing

**Build the package locally:**
```bash
poetry build
```

This creates distribution files in the `dist/` directory.

**Publishing workflow (for maintainers):**

The project uses GitHub Actions for automated publishing. To release:

1. Update version in `pyproject.toml`
2. Create a new Git tag: `git tag v0.1.6`
3. Push the tag: `git push origin v0.1.6`
4. The release workflow will automatically publish to PyPI

**Manual publishing (if needed):**
```bash
# Configure PyPI token
poetry config pypi-token.pypi <your-token>

# Publish to PyPI
poetry publish

# Or publish to test PyPI first
poetry config repositories.testpypi https://test.pypi.org/legacy/
poetry publish -r testpypi
```


## Virtual Environment Installation

For isolated installation without affecting your system Python:

### Using venv (Built-in)

```bash
# Create virtual environment
python -m venv codeql-wrapper-env

# Activate virtual environment
# On Linux/macOS:
source codeql-wrapper-env/bin/activate
# On Windows:
codeql-wrapper-env\Scripts\activate

# Install CodeQL Wrapper
pip install codeql-wrapper

# Verify installation
codeql-wrapper --version
```

### Using conda

```bash
# Create conda environment
conda create -n codeql-wrapper python=3.12

# Activate environment
conda activate codeql-wrapper

# Install CodeQL Wrapper
pip install codeql-wrapper

# Verify installation
codeql-wrapper --version
```

## Container Installation

CodeQL Wrapper can be run in containerized environments:

### Docker Example

Create a Dockerfile:

```dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install CodeQL Wrapper
RUN pip install codeql-wrapper

# Create non-root user for security
RUN useradd -m -u 1001 codeql
USER codeql

# Set entrypoint
ENTRYPOINT ["codeql-wrapper"]
```

Build and run:

```bash
# Build the image
docker build -t codeql-wrapper .

# Run analysis on a mounted repository
docker run --rm -v /path/to/repo:/workspace codeql-wrapper analyze /workspace

# Run with output directory
docker run --rm -v /path/to/repo:/workspace -v /path/to/output:/output \
    codeql-wrapper analyze /workspace --output-dir /output
```

### CI/CD Container Usage

For CI/CD pipelines, you can use CodeQL Wrapper in any Python container:

```yaml
# GitHub Actions example
- name: Run CodeQL Analysis
  run: |
    pip install codeql-wrapper
    codeql-wrapper analyze . --upload-sarif
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Verification

After installation, verify that CodeQL Wrapper is working correctly:

```bash
# Check version
codeql-wrapper --version

# View help
codeql-wrapper --help

# Test basic functionality
codeql-wrapper analyze --help
```

Expected output should show version 0.1.5 and available commands.

## Troubleshooting

### Python Version Issues

If you encounter Python version compatibility issues:

```bash
# Check your Python version
python --version

# CodeQL Wrapper requires Python 3.8.1 or higher
# Upgrade Python if needed
```

### Package Installation Problems

If pip installation fails:

```bash
# Try upgrading pip
python -m pip install --upgrade pip

# Install with verbose output to see detailed error messages
pip install -v codeql-wrapper

# For development dependencies, install from source
git clone https://github.com/your-org/codeql-wrapper.git
cd codeql-wrapper
pip install -e .
```

### Platform-Specific Issues

**Windows:**
- Ensure you're using a compatible shell (PowerShell, Command Prompt, or Git Bash)
- Some antivirus software may interfere with CodeQL CLI downloads

**macOS:**
- On Apple Silicon Macs, CodeQL Wrapper automatically detects the architecture
- Ensure Xcode Command Line Tools are installed: `xcode-select --install`

**Linux:**
- Ensure you have the necessary permissions for CodeQL CLI installation
- Some distributions may require additional system packages

### Permission Issues

If you encounter permission errors:

```bash
# Install for current user only
pip install --user codeql-wrapper

# Or use virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install codeql-wrapper
```

### CodeQL CLI Issues

CodeQL Wrapper automatically downloads and manages CodeQL CLI. If you encounter issues:

- Check internet connectivity
- Verify firewall/proxy settings don't block GitHub releases
- Ensure sufficient disk space for CodeQL CLI download (~500MB)

### Poetry-Specific Issues

When installing from source using Poetry:

```bash
# If Poetry is not in PATH
export PATH="$HOME/.local/bin:$PATH"

# If you encounter dependency resolution issues
poetry lock --no-update
poetry install

# Clear Poetry cache if needed
poetry cache clear --all pypi
```

For additional support, check the [GitHub Issues](https://github.com/ModusCreate-Perdigao-GHAS-Playground/codeql-wrapper/issues) page or create a new issue with detailed error information.
