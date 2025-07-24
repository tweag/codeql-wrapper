# CodeQL Wrapper

<div align="center">

[![Lint](https://github.com/ModusCreate-Perdigao-GHAS-Playground/codeql-wrapper/actions/workflows/lint.yml/badge.svg)](https://github.com/ModusCreate-Perdigao-GHAS-Playground/codeql-wrapper/actions/workflows/lint.yml)
[![Build](https://github.com/ModusCreate-Perdigao-GHAS-Playground/codeql-wrapper/actions/workflows/build.yml/badge.svg)](https://github.com/ModusCreate-Perdigao-GHAS-Playground/codeql-wrapper/actions/workflows/build.yml)
[![PyPI version](https://badge.fury.io/py/codeql-wrapper.svg)](https://badge.fury.io/py/codeql-wrapper)
[![Python versions](https://img.shields.io/pypi/pyversions/codeql-wrapper.svg)](https://pypi.org/project/codeql-wrapper/)
[![Documentation](https://img.shields.io/badge/docs-available-brightgreen.svg)](https://moduscreate-perdigao-ghas-playground.github.io/codeql-wrapper/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

***

> **A universal Python CLI wrapper for running CodeQL analysis seamlessly across any project architecture and CI/CD platform.**

**CodeQL Wrapper** simplifies security analysis by providing a unified interface for CodeQL across monorepos, single repositories, and diverse CI/CD environments including Jenkins, GitHub Actions, Harness, Azure DevOps, and more.

## Features

<table>
<tr>
<td width="50%" valign=top>

**Universal Support**\
Works with both monorepos and single repositories

**CI/CD Agnostic**\
Seamless integration across all major CI/CD platforms

**Smart Language Detection**\
Automatically detects and analyzes multiple programming languages

**SARIF Integration**\
Built-in support for SARIF upload to GitHub Advanced Security

</td>
<td width="50%" valign=top>

**Performance Optimized**\
Parallel processing and intelligent resource management

**Auto-Installation**\
Automatically downloads and manages CodeQL CLI

**Flexible Configuration**\
JSON-based configuration for complex project structures

</td>
</tr>
</table>

## Prerequisites

| Requirement | Version/Details |
|-------------|-----------------|
| **Python** | 3.9 or higher |
| **Git** | For repository analysis |
| **GitHub Token** | Required for SARIF upload functionality |

***

## Quick Start

### Installation

Install CodeQL Wrapper from PyPI:

```bash
pip install codeql-wrapper
```

### Basic Usage

#### Single Repository Analysis

Analyze a single repository with automatic language detection:

```bash
codeql-wrapper analyze /path/to/repository
```

#### Monorepo Analysis

Analyze all projects in a monorepo "using build-mode none" and upload results to GitHub Advanced Security:

```bash
codeql-wrapper analyze /path/to/monorepo --monorepo --upload-sarif
```

#### Targeted Analysis

Analyze only projects with changes (perfect for CI/CD):

```bash
codeql-wrapper analyze /path/to/repo --monorepo --only-changed-files --upload-sarif
```

> **Note**: Ensure your `GITHUB_TOKEN` environment variable is set for SARIF upload functionality.

***

## Advanced Configuration

For complex monorepo setups, create a `.codeql.json` configuration file in your repository root:

<details>
<summary><strong>Click to view example configuration</strong></summary>

```json
{
  "projects": [
    {
      "path": "./monorepo/project-java-1",
      "build-mode": "manual",
      "build-script": "./build/project-java-1.sh",
      "queries": ["java-security-extended"],
      "language": "java"
    },
    {
      "path": "./monorepo/project-java-1", 
      "language": "javascript"
    },
    {
      "path": "./monorepo/project-python-1",
      "build-mode": "none"
    },
    {
      "path": "./monorepo/project-python-javascript-cpp",
      "build-mode": "none",
      "language": "javascript"
    }
  ]
}
```

</details>

### Configuration Options

| Option | Description | Values |
|--------|-------------|---------|
| `path` | Relative path to the project | Any valid path |
| `build-mode` | How to build the project (default=none) | `none`, `manual`, `autobuild` |
| `build-script` | Custom build script path | Path to executable script |
| `queries` | CodeQL query suites to run | Array of query suite names |
| `language` | Target language (default=auto-detect) | Any supported language |

***

## CI/CD Integration

| Platform | Status |
|----------|--------|
| **GitHub Actions** | ✅ Supported |
| **Harness** | ✅ Supported |
| **Circle CI** | ✅ Supported |
| **Azure Pipelines** | ✅ Supported |
| **Jenkins** | ✅ Supported |

**Examples and implementation guides available at:**\
<https://github.com/ModusCreate-fernandomatsuo-GHAS/poc-codeql-wrapper>

***

## Documentation

**Complete documentation is available at:**\
<https://moduscreate-perdigao-ghas-playground.github.io/codeql-wrapper>

***

## Contributing

We welcome contributions! Please see the [contributing guidelines](CONTRIBUTING.md) for more information.

***

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

***

<div align="center">

**Made with ❤️ by the Modus Create team**

</div>
