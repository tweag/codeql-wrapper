---
sidebar_position: 3
---

# CLI Usage

Complete command-line reference for CodeQL Wrapper.

## Basic Commands

### Analyze Command

The main command for running CodeQL analysis:

```bash
codeql-wrapper analyze [OPTIONS] REPOSITORY_PATH
```

#### Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--languages` | `-l` | Comma-separated list of languages to analyze | All detected |
| `--output-dir` | `-o` | Output directory for results | `./codeql-results` |
| `--monorepo` | | Treat as monorepo (analyze sub-projects) | `false` |
| `--force-install` | | Force CodeQL reinstallation using the latest version| `false` |
| `--upload-sarif` | | Upload SARIF results to GitHub | `false` |
| `--repository` | | GitHub repository (owner/repo) | Auto-detected |
| `--commit-sha` | | Git commit SHA | Auto-detected |
| `--ref` | | Git reference (branch/tag) | Auto-detected |
| `--github-token` | | GitHub token for SARIF upload | `$GITHUB_TOKEN` |
| `--verbose` | `-v` | Enable verbose logging | `false` |
| `--only-changed-files` | | Only analyze projects with changed files (monorepo only) | `false` |
| `--max-workers` | | Maximum number of parallel workers for analysis | Auto-detected |
| `--build-mode` | | Build mode for compiled languages (e.g., "autobuild", "none") | `none` |
| `--build-script` | | Path to a custom build script | None |
| `--queries` | | Comma-separated list of CodeQL query suite paths or names | Default |

### Examples

#### Single Repository Analysis

```bash
# Basic analysis
codeql-wrapper analyze /path/to/repository

# Analyze specific languages only
codeql-wrapper analyze /path/to/repo --languages python,javascript

# Custom output directory
codeql-wrapper analyze /path/to/repo --output-dir /path/to/results

# Force CodeQL reinstallation using the latest CodeQL version before runing the analyze 
codeql-wrapper analyze /path/to/repo --force-install

# Verbose output
codeql-wrapper analyze /path/to/repo --verbose
```

#### Monorepo Analysis

```bash
# Analyze all sub-projects in a monorepo
codeql-wrapper analyze /path/to/monorepo --monorepo

# Analyze only changed files in a monorepo
codeql-wrapper analyze /path/to/monorepo --monorepo --only-changed-files

# Analyze with a custom build script and specific queries
codeql-wrapper analyze /path/to/monorepo --monorepo --build-script ./build.sh --queries security-and-quality,my-custom-queries
```

#### SARIF Upload

```bash
# Analyze and upload (auto-detects Git info)
codeql-wrapper analyze /path/to/repo --upload-sarif

# With explicit parameters
codeql-wrapper analyze /path/to/repo \
  --upload-sarif \
  --repository owner/repository \
  --commit-sha $COMMIT_SHA \
  --ref refs/heads/main
```

### Install Command

Install or update CodeQL:

```bash
codeql-wrapper install [OPTIONS]
```

#### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--version` | `-v` | Specific CodeQL version to install |
| `--force` | `-f` | Force reinstallation |

#### Examples

```bash
# Install latest CodeQL
codeql-wrapper install

# Install specific version
codeql-wrapper install --version 2.15.0

# Force reinstallation
codeql-wrapper install --force
```

### Upload SARIF Command

Upload SARIF files to GitHub Code Scanning:

```bash
codeql-wrapper upload-sarif [OPTIONS] SARIF_FILES...
```

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--repository` | GitHub repository (owner/repo) | Auto-detected |
| `--commit-sha` | Git commit SHA | Auto-detected |
| `--ref` | Git reference | Auto-detected |
| `--github-token` | GitHub token | `$GITHUB_TOKEN` |

#### Examples

```bash
# Upload with auto-detection (single file)
codeql-wrapper upload-sarif results.sarif

# Upload multiple SARIF files
codeql-wrapper upload-sarif results-python.sarif results-java.sarif

# Upload with explicit parameters
codeql-wrapper upload-sarif results.sarif \
  --repository owner/repo \
  --commit-sha abc123 \
  --ref refs/heads/main
```

## Global Options

These options work with all commands:

| Option | Short | Description |
|--------|-------|-------------|
| `--help` | `-h` | Show help message |
| `--version` | | Show version |
| `--verbose` | `-v` | Enable verbose logging |

## Supported Languages

CodeQL Wrapper supports analysis for the following languages:

- **JavaScript/TypeScript** - `.js`, `.ts`, `.jsx`, `.tsx`
- **Python** - `.py`
- **Java** - `.java`
- **C#** - `.cs`
- **C/C++** - `.c`, `.cpp`, `.h`, `.hpp`
- **Go** - `.go`
- **Ruby** - `.rb`
- **Swift** - `.swift`
- **Kotlin** - `.kt`, `.kts`
- **GitHub Actions** - `.yml`, `.yaml` (in `.github/workflows/`)

## Environment Variables

CodeQL Wrapper uses these environment variables:

| Variable | Description |
|----------|-------------|
| `GITHUB_TOKEN` | GitHub token for SARIF upload |
| `CODEQL_DIST` | CodeQL installation directory (auto-set) |
| `CODEQL_REPO` | CodeQL search paths (auto-set) |

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | General error |
| `2` | Invalid arguments |
| `3` | Analysis failure |
| `4` | Upload failure |

## Configuration Files

Currently, CodeQL Wrapper doesn't use configuration files, but you can create shell scripts or batch files to standardize your usage:

### Example Script

```bash
#!/bin/bash
# analyze-repo.sh

REPO_PATH=${1:-"."}
OUTPUT_DIR=${2:-"./security-results"}

codeql-wrapper analyze "$REPO_PATH" \
  --output-dir "$OUTPUT_DIR" \
  --upload-sarif \
  --verbose
```

Usage:

```bash
chmod +x analyze-repo.sh
./analyze-repo.sh /path/to/repo
```


