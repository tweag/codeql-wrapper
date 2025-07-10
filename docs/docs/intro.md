---
sidebar_position: 1
---

# Getting Started

Welcome to **CodeQL Wrapper** - a universal Python CLI wrapper for running CodeQL analysis on any type of project across different CI/CD platforms.

## What is CodeQL Wrapper?

CodeQL Wrapper is a Python-based tool that simplifies running CodeQL security analysis on your projects. It provides:

- **Smart Project Detection**: Automatically identifies single-project repositories or monorepos with multiple projects, detecting languages and structure
- **Auto-Managed CodeQL Installation**: Automatically downloads, installs, and manages CodeQL CLI and query packs
- **Multi-Platform CI/CD**: Works seamlessly with Jenkins, GitHub Actions, Harness, and other CI/CD tools
- **Parallel Processing**: Run analysis on multiple projects concurrently
- **SARIF Upload**: Built-in integration with GitHub Code Scanning

## Quick Start

### Installation

Install CodeQL Wrapper from PyPI:

```bash
pip install codeql-wrapper
```

Or install from source:

```bash
git clone https://github.com/ModusCreate-Perdigao-GHAS-Playground/codeql-wrapper.git
cd codeql-wrapper
poetry install
```

### Basic Usage

Analyze a single repository:

```bash
codeql-wrapper analyze /path/to/repository
```

Analyze a monorepo:

```bash
codeql-wrapper analyze /path/to/monorepo --monorepo
```

Analyze and upload results to GitHub Code Scanning:

```bash
codeql-wrapper analyze /path/to/repo --upload-sarif
```

## What You'll Need

- **Python 3.8.1 or higher**
- **Git** (for repository analysis)
- **GitHub Token** (for SARIF upload functionality)

## Next Steps

- [Installation Guide](./installation) - Detailed installation instructions
- [CLI Usage](./cli-usage) - Complete command-line reference
- [CI/CD Integration](./cicd-integration) - Integration with various CI/CD platforms
- [API Reference](./api) - Python API documentation
