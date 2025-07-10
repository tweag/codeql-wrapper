---
sidebar_position: 1
---

# Getting Started

Welcome to **CodeQL Wrapper** - a universal Python CLI wrapper that simplifies running CodeQL security analysis on any type of project across different CI/CD platforms.

## What is CodeQL Wrapper?

CodeQL Wrapper is a powerful Python-based tool designed to streamline security analysis workflows. It eliminates the complexity of manually managing CodeQL installations and configurations while providing enterprise-grade features for modern development teams.

### Key Features

- **Smart Project Detection**: Automatically identifies single-project repositories or monorepos with multiple projects, detecting languages and project structure
- **Auto-Managed CodeQL Installation**: Automatically downloads, installs, and manages CodeQL CLI and query packs - no manual setup required
- **Multi-Platform CI/CD**: Works seamlessly with Jenkins, GitHub Actions, Azure DevOps, Harness, and other CI/CD platforms
- **Parallel Processing**: Run analysis on multiple projects concurrently for faster results
- **SARIF Upload**: Built-in integration with GitHub Code Scanning for seamless security reporting
- **Multi-Language Support**: Supports JavaScript/TypeScript, Python, Java, C#, C/C++, Go, Ruby, Swift, and GitHub Actions
- **Flexible Configuration**: Support for both automatic detection and custom project configurations

## Quick Start

### Prerequisites

Before you begin, ensure you have:

- **Python 3.8.1 or higher** installed
- **Git** for repository analysis
- **GitHub Token** (optional, for SARIF upload functionality)

### Installation

#### Option 1: Install from PyPI (Recommended)

```bash
pip install codeql-wrapper
```

#### Option 2: Install from Source

```bash
git clone https://github.com/ModusCreate-Perdigao-GHAS-Playground/codeql-wrapper.git
cd codeql-wrapper
poetry install
```

### Verify Installation

```bash
codeql-wrapper --version
```

## Usage Examples

### 1. Single Repository Analysis

Analyze a single repository with automatic language detection:

```bash
codeql-wrapper analyze /path/to/repository
```

**Example output:**
```
=== CodeQL Analysis Results ===
Repository: /path/to/repository
Projects detected: 1
Analyses completed: 1/1
Success rate: 100.00%
Total findings: 5
```

### 2. Monorepo Analysis (Auto-Discovery)

Analyze a monorepo where each subfolder is treated as a separate project:

```bash
codeql-wrapper analyze /path/to/monorepo --monorepo
```

This will automatically scan all subdirectories and analyze each project independently.

### 3. Monorepo Analysis (Configuration-Based)

For complex monorepos, create a `.codeql.json` configuration file in the root directory:

```json
{
    "projects": [
        {
            "path": "./backend/api-service",
            "build-mode": "manual",
            "build-script": "./scripts/build-api.sh",
            "queries": [
                "java-security-extended"
            ]
        },
        {
            "path": "./frontend/web-app",
            "build-mode": "none",
            "queries": [
                "javascript-security-and-quality"
            ]
        },
        {
            "path": "./data-processing",
            "build-mode": "none"
        }
    ]
}
```

Then run:

```bash
codeql-wrapper analyze /path/to/monorepo --monorepo
```

### 4. Language-Specific Analysis

Analyze only specific languages:

```bash
codeql-wrapper analyze /path/to/repo --languages python,javascript
```

### 5. Custom Output Directory

Specify where to save analysis results:

```bash
codeql-wrapper analyze /path/to/repo --output-dir ./security-results
```

### 6. GitHub Code Scanning Integration

Analyze and automatically upload results to GitHub Code Scanning:

```bash
# Using environment variables
export GITHUB_TOKEN=your_github_token
codeql-wrapper analyze /path/to/repo --upload-sarif

# Or specify parameters explicitly
codeql-wrapper analyze /path/to/repo \
  --upload-sarif \
  --repository owner/repo-name \
  --commit-sha abc123def456 \
  --github-token your_token
```

## Configuration Options

### Build Modes

- **`none`**: For interpreted languages (Python, JavaScript, etc.) that don't require compilation
- **`manual`**: For compiled languages with custom build scripts
- **`autobuild`**: Let CodeQL attempt to automatically build the project

### Query Suites

Available query suites include:
- `security-extended`: Comprehensive security analysis
- `security-and-quality`: Security + code quality checks
- `code-scanning`: GitHub's default code scanning queries

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GITHUB_TOKEN` | GitHub personal access token for SARIF upload | None |
| `CODEQL_DIST` | Custom CodeQL installation directory | Auto-managed |

## Supported Languages

CodeQL Wrapper supports analysis for the following languages:

| Language | File Extensions | Notes |
|----------|----------------|-------|
| JavaScript/TypeScript | `.js`, `.ts`, `.jsx`, `.tsx` | Includes Node.js and browser code |
| Python | `.py` | Python 2 and 3 support |
| Java | `.java` | Java 8+ with Maven/Gradle support |
| C# | `.cs` | .NET Framework and .NET Core |
| C/C++ | `.c`, `.cpp`, `.h`, `.hpp` | Cross-platform support |
| Go | `.go` | Go modules supported |
| Ruby | `.rb` | Ruby 2.5+ |
| Swift | `.swift` | iOS/macOS development |
| GitHub Actions | `.yml`, `.yaml` (in `.github/workflows/`) | Workflow security analysis |

## Common Use Cases

### Security Team Workflows

```bash
# Weekly security scan of all repositories
codeql-wrapper analyze /repos/critical-app --languages java,javascript --upload-sarif

# Compliance reporting with custom output
codeql-wrapper analyze /repos/financial-service --output-dir ./compliance-reports
```

### CI/CD Integration

```bash
# Jenkins Pipeline
codeql-wrapper analyze $WORKSPACE --upload-sarif --repository $GIT_REPO

# GitHub Actions (see CI/CD Integration guide for complete workflows)
codeql-wrapper analyze . --upload-sarif
```

### Development Team Usage

```bash
# Quick local security check before commit
codeql-wrapper analyze . --languages python

# Full analysis with verbose output for debugging
codeql-wrapper analyze . --verbose --force-install
```

## What You'll Need

- **Python 3.8.1 or higher**
- **Git** (for repository analysis)
- **GitHub Token** (for SARIF upload functionality)

## Troubleshooting

### Common Issues

1. **Permission Errors**: Ensure you have read access to the repository and write access to the output directory
2. **Build Failures**: For compiled languages, verify that build dependencies are available
3. **Large Repositories**: Consider using `--languages` to limit analysis scope for faster results

### Getting Help

- Check the verbose output: `codeql-wrapper analyze /path/to/repo --verbose`
- Verify CodeQL installation: `codeql-wrapper install --force`
- Review configuration: Ensure `.codeql.json` syntax is valid for monorepos

## Next Steps

Ready to dive deeper? Explore these resources:

- [**Installation Guide**](./installation) - Detailed installation instructions and setup options
- [**CLI Usage**](./cli-usage) - Complete command-line reference with examples
- [**CI/CD Integration**](./cicd-integration) - Integration guides for Jenkins, GitHub Actions, Azure DevOps, and more
- [**API Reference**](./api) - Python API documentation for programmatic usage

### Quick Links

- **Need help with monorepo configuration?** → [Configuration Examples](./cli-usage#monorepo-configuration)
- **Setting up GitHub Code Scanning?** → [SARIF Upload Guide](./cicd-integration#github-actions)
- **Troubleshooting build issues?** → [Common Problems](./installation#troubleshooting)
- **Want to contribute?** → [GitHub Repository](https://github.com/ModusCreate-Perdigao-GHAS-Playground/codeql-wrapper)

---

**Ready to secure your code?** Start with a simple analysis:

```bash
pip install codeql-wrapper
codeql-wrapper analyze .
```
