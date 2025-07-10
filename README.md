# CodeQL Wrapper

[![Tests](https://github.com/ModusCreate-Perdigao-GHAS-Playground/codeql-wrapper/actions/workflows/test.yml/badge.svg)](https://github.com/ModusCreate-Perdigao-GHAS-Playground/codeql-wrapper/actions/workflows/test.yml)
[![Lint](https://github.com/ModusCreate-Perdigao-GHAS-Playground/codeql-wrapper/actions/workflows/lint.yml/badge.svg)](https://github.com/ModusCreate-Perdigao-GHAS-Playground/codeql-wrapper/actions/workflows/lint.yml)
[![Build](https://github.com/ModusCreate-Perdigao-GHAS-Playground/codeql-wrapper/actions/workflows/build.yml/badge.svg)](https://github.com/ModusCreate-Perdigao-GHAS-Playground/codeql-wrapper/actions/workflows/build.yml)
[![PyPI version](https://badge.fury.io/py/codeql-wrapper.svg)](https://badge.fury.io/py/codeql-wrapper)
[![Python versions](https://img.shields.io/pypi/pyversions/codeql-wrapper.svg)](https://pypi.org/project/codeql-wrapper/)
[![Documentation](https://img.shields.io/badge/docs-available-brightgreen.svg)](https://moduscreate-perdigao-ghas-playground.github.io/codeql-wrapper/)

A universal Python CLI wrapper for running CodeQL analysis on any type of project (monorepo or single repository) across different CI/CD platforms including Jenkins, GitHub Actions, Harness, and any environment where Python scripts can be executed.

## Features

- **Universal Support**: Works with monorepos and single repositories
- **Multi-Platform**: Supports Linux, macOS, and Windows
- **Language Detection**: Automatically detects supported languages in your codebase
- **CI/CD Integration**: Seamlessly integrates with popular CI/CD platforms
- **SARIF Upload**: Direct upload to GitHub Code Scanning
- **Easy Installation**: Simple pip installation with minimal dependencies

## Supported Languages

- **JavaScript/TypeScript** - `.js`, `.ts`, `.tsx`, `.mts`, `.cts`
- **Python** - `.py`
- **Java** - `.java`
- **C#** - `.cs`, `.cshtml`, `.xaml`, `.sln`, `.csproj`
- **C/C++** - `.c`, `.cpp`, `.h`, `.hpp`, `.c++`, `.cxx`, `.hh`, `.h++`, `.hxx`, `.cc`
- **Go** - `.go`
- **Ruby** - `.rb`
- **Swift** - `.swift`
- **GitHub Actions** - `.yml`, `.yaml` (in `.github/workflows/`)

## Quick Start

### Installation

```bash
pip install codeql-wrapper
```

### Basic Usage

```bash
# Analyze current directory
codeql-wrapper analyze .

# Analyze specific repository
codeql-wrapper analyze /path/to/your/repo

# Analyze with verbose output
codeql-wrapper analyze . --verbose
```

### Monorepo Analysis

```bash
# Analyze all projects in a monorepo
codeql-wrapper analyze . --monorepo --verbose
```

#### Monorepo Configuration with .codeql.json

For complex monorepos, you can create a `.codeql.json` configuration file in your repository root to define project structure and analysis settings:

```json
{
  "name": "My Monorepo",
  "projects": [
    {
      "name": "frontend-app",
      "path": "./apps/frontend",
      "languages": ["javascript", "typescript"]
    },
    {
      "name": "backend-api",
      "path": "./services/backend-api",
      "build-mode": "manual",
      "build-script": "./build/backend-api.sh",
      "queries": [
        "java-security-extended"
      ]
    }
  ]
}
```

When you have a `.codeql.json` file, CodeQL Wrapper will:
1. Automatically detect the configuration
2. Analyze each defined project separately
3. Generate individual reports for each project
4. Combine results for comprehensive coverage

Example monorepo analysis with configuration:

```bash
# The wrapper will automatically use .codeql.json if present
codeql-wrapper analyze . --monorepo

# Output structure:
# codeql-results/
# ├── backend-api/
# │   ├── python-results.sarif
# │   └── javascript-results.sarif
# ├── frontend-app/
# │   ├── javascript-results.sarif
# │   └── typescript-results.sarif
# ├── mobile-app/
# │   ├── java-results.sarif
# │   └── swift-results.sarif
# └── shared-libs/
#     ├── typescript-results.sarif
#     └── python-results.sarif
```

## Requirements

- **Python**: 3.8.1 or higher
- **Operating System**: Linux, macOS, or Windows
- **Git**: Required for repository analysis and auto-detection
- **Internet Connection**: For CodeQL CLI download and SARIF upload

## Documentation

Complete documentation is available at: **https://moduscreate-perdigao-ghas-playground.github.io/codeql-wrapper/**

### Documentation Sections

- [Installation Guide](https://moduscreate-perdigao-ghas-playground.github.io/codeql-wrapper/docs/installation)
- [CLI Usage](https://moduscreate-perdigao-ghas-playground.github.io/codeql-wrapper/docs/cli-usage)
- [API Reference](https://moduscreate-perdigao-ghas-playground.github.io/codeql-wrapper/docs/api)
- [CI/CD Integration](https://moduscreate-perdigao-ghas-playground.github.io/codeql-wrapper/docs/cicd-integration)

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and quality checks:
   ```bash
   poetry run pytest --cov=src/codeql_wrapper
   poetry run black src/ tests/
   poetry run mypy src/
   poetry run flake8 src/ tests/
   ```
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Setup

```bash
# Clone the repository
git clone https://github.com/ModusCreate-Perdigao-GHAS-Playground/codeql-wrapper.git
cd codeql-wrapper

# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install --with dev

# Run tests
poetry run pytest
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/ModusCreate-Perdigao-GHAS-Playground/codeql-wrapper/issues)
- **Documentation**: [Official Documentation](https://moduscreate-perdigao-ghas-playground.github.io/codeql-wrapper/)
- **PyPI**: [codeql-wrapper on PyPI](https://pypi.org/project/codeql-wrapper/)

## Authors

- **Mateus Perdigão Domiciano** - [mateus.domiciano@moduscreate.com](mailto:mateus.domiciano@moduscreate.com)
- **Fernando Matsuo Santos** - [fernando.matsuo@moduscreate.com](mailto:fernando.matsuo@moduscreate.com)
