---
sidebar_position: 3
---

# CLI Usage

Complete command-line reference for CodeQL Wrapper.

## Overview

CodeQL Wrapper is a universal Python CLI tool for running CodeQL analysis on any project type, including monorepos and single repositories, across different CI/CD platforms.

## Commands

### Global Options

These options work with all commands:

| Option | Short | Description |
|--------|-------|-------------|
| `--help` | `-h` | Show help message |
| `--version` | `-V` | Show version and exit |
| `--verbose` | `-v` | Enable verbose logging |

### Main Commands

CodeQL Wrapper provides three main commands:

1. **`analyze`** - Run CodeQL analysis on a repository
2. **`install`** - Install or update CodeQL CLI
3. **`upload-sarif`** - Upload SARIF files to GitHub Code Scanning

## Analyze Command

The primary command for running CodeQL analysis:

```bash
codeql-wrapper analyze [OPTIONS] REPOSITORY_PATH
```

### Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--languages` | `-l` | Comma-separated list of languages to analyze | All detected |
| `--output-dir` | `-o` | Output directory for results | `./codeql-results` |
| `--monorepo` | | Treat as monorepo (analyze sub-projects) | `false` |
| `--force-install` | | Force reinstallation of latest CodeQL version | `false` |
| `--upload-sarif` | | Upload SARIF results to GitHub Code Scanning | `false` |
| `--repository` | | GitHub repository (owner/repo) for SARIF upload | Auto-detected |
| `--commit-sha` | | Git commit SHA for SARIF upload | Auto-detected |
| `--ref` | | Git reference (branch/tag) for SARIF upload | Auto-detected |
| `--github-token` | | GitHub token for SARIF upload | `$GITHUB_TOKEN` |

### Examples

#### Basic Analysis

```bash
# Analyze current directory
codeql-wrapper analyze .

# Analyze specific repository
codeql-wrapper analyze /path/to/repository

# Analyze with verbose output
codeql-wrapper analyze /path/to/repo --verbose
```

#### Language-Specific Analysis

```bash
# Analyze specific languages only
codeql-wrapper analyze /path/to/repo --languages python,javascript

# Analyze multiple languages
codeql-wrapper analyze /path/to/repo --languages java,csharp,cpp
```

#### Output Control

```bash
# Custom output directory
codeql-wrapper analyze /path/to/repo --output-dir /path/to/results

# Force CodeQL reinstallation before analysis
codeql-wrapper analyze /path/to/repo --force-install
```

#### Monorepo Analysis

```bash
# Analyze all sub-projects in a monorepo
codeql-wrapper analyze /path/to/monorepo --monorepo
```

#### SARIF Upload Integration

```bash
# Analyze and upload results (auto-detects Git information)
codeql-wrapper analyze /path/to/repo --upload-sarif

# Upload with explicit GitHub repository details
codeql-wrapper analyze /path/to/repo \
  --upload-sarif \
  --repository owner/repository \
  --commit-sha $COMMIT_SHA \
  --ref refs/heads/main \
  --github-token $GITHUB_TOKEN
```

## Install Command

Install or update the CodeQL CLI:

```bash
codeql-wrapper install [OPTIONS]
```

### Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--version` | `-V` | Specific CodeQL version to install | `v2.22.1` |
| `--force` | | Force reinstallation even if already installed | `false` |

### Examples

```bash
# Install latest CodeQL version
codeql-wrapper install

# Install specific version
codeql-wrapper install --version v2.21.0

# Force reinstallation
codeql-wrapper install --force

# Install specific version with force
codeql-wrapper install --version v2.20.0 --force
```

## Upload SARIF Command

Upload SARIF files to GitHub Code Scanning:

```bash
codeql-wrapper upload-sarif [OPTIONS] SARIF_FILE
```

### Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--repository` | `-r` | GitHub repository (owner/repo) | Auto-detected |
| `--commit-sha` | `-c` | Git commit SHA | Auto-detected |
| `--ref` | | Git reference (branch/tag) | Auto-detected |
| `--github-token` | | GitHub token for authentication | `$GITHUB_TOKEN` |

### Examples

```bash
# Upload with auto-detection
codeql-wrapper upload-sarif results.sarif

# Upload with explicit parameters
codeql-wrapper upload-sarif results.sarif \
  --repository owner/repo \
  --commit-sha abc123def456 \
  --ref refs/heads/main

# Upload with custom GitHub token
codeql-wrapper upload-sarif results.sarif \
  --github-token ghp_your_token_here
```

## Supported Languages

CodeQL Wrapper automatically detects and analyzes the following languages:

### Non-Compiled Languages
- **JavaScript** - `.js` files
- **TypeScript** - `.ts`, `.tsx`, `.mts`, `.cts` files
- **Python** - `.py` files
- **Ruby** - `.rb` files
- **GitHub Actions** - `.yml`, `.yaml` files in `.github/workflows/`

### Compiled Languages
- **Java** - `.java` files
- **C#** - `.cs`, `.cshtml`, `.xaml` files, `.sln`, `.csproj` projects
- **C/C++** - `.c`, `.cpp`, `.h`, `.hpp`, `.c++`, `.cxx`, `.hh`, `.h++`, `.hxx`, `.cc` files
- **Go** - `.go` files
- **Swift** - `.swift` files
- **Kotlin** - `.kt` files (entity support)

### Language Selection

You can specify languages to analyze using the `--languages` option:

```bash
# Analyze only Python and JavaScript
codeql-wrapper analyze . --languages python,javascript

# Analyze compiled languages
codeql-wrapper analyze . --languages java,csharp,cpp

# Mix of compiled and non-compiled
codeql-wrapper analyze . --languages python,java,typescript
```

**Note:** Language names are case-insensitive. Use the following identifiers:
- `javascript`, `typescript`, `python`, `ruby`, `actions`
- `java`, `csharp`, `cpp`, `go`, `swift`, `kotlin`

## Environment Variables

CodeQL Wrapper recognizes these environment variables:

| Variable | Description | Usage |
|----------|-------------|-------|
| `GITHUB_TOKEN` | GitHub token for SARIF upload | Required for `--upload-sarif` |
| `CODEQL_DIST` | CodeQL installation directory | Auto-managed by wrapper |
| `CODEQL_REPO` | CodeQL search paths | Auto-managed by wrapper |

### Setting Environment Variables

**Linux/macOS:**
```bash
export GITHUB_TOKEN=ghp_your_token_here
codeql-wrapper analyze . --upload-sarif
```

**Windows PowerShell:**
```powershell
$env:GITHUB_TOKEN = "ghp_your_token_here"
codeql-wrapper analyze . --upload-sarif
```

**Windows Command Prompt:**
```cmd
set GITHUB_TOKEN=ghp_your_token_here
codeql-wrapper analyze . --upload-sarif
```

## Exit Codes

CodeQL Wrapper uses standard exit codes to indicate operation results:

| Code | Meaning | Description |
|------|---------|-------------|
| `0` | Success | Operation completed successfully |
| `1` | Error | General error or failure |

### Common Exit Scenarios

**Success (0):**
- Analysis completed successfully
- CodeQL installed successfully
- SARIF uploaded successfully

**Error (1):**
- Invalid arguments or options
- Missing required parameters (e.g., GitHub token for SARIF upload)
- Analysis failure
- Upload failure
- Installation failure
- Git repository not found or invalid

## Advanced Usage

### Automation Scripts

Create reusable scripts for common workflows:

**analyze-and-upload.sh:**
```bash
#!/bin/bash
# Comprehensive analysis and upload script

REPO_PATH="${1:-.}"
OUTPUT_DIR="${2:-./security-results}"
LANGUAGES="${3:-}"

# Build command
CMD="codeql-wrapper analyze \"$REPO_PATH\" --output-dir \"$OUTPUT_DIR\" --upload-sarif --verbose"

# Add languages if specified
if [ -n "$LANGUAGES" ]; then
    CMD="$CMD --languages \"$LANGUAGES\""
fi

# Execute
echo "Running: $CMD"
eval $CMD
```

**analyze-monorepo.ps1:**
```powershell
# PowerShell script for monorepo analysis
param(
    [string]$RepoPath = ".",
    [string]$OutputDir = "./security-results",
    [string]$Languages = ""
)

$cmd = "codeql-wrapper analyze `"$RepoPath`" --monorepo --output-dir `"$OutputDir`" --verbose"

if ($Languages) {
    $cmd += " --languages `"$Languages`""
}

Write-Host "Executing: $cmd"
Invoke-Expression $cmd
```

### CI/CD Integration

**GitHub Actions:**
```yaml
- name: CodeQL Analysis
  run: |
    pip install codeql-wrapper
    codeql-wrapper analyze . --upload-sarif --verbose
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**GitLab CI:**
```yaml
codeql_analysis:
  script:
    - pip install codeql-wrapper
    - codeql-wrapper analyze . --output-dir ./codeql-results
  artifacts:
    paths:
      - codeql-results/
```

**Jenkins:**
```groovy
stage('CodeQL Analysis') {
    steps {
        sh 'pip install codeql-wrapper'
        sh 'codeql-wrapper analyze . --output-dir ./codeql-results'
        archiveArtifacts artifacts: 'codeql-results/**/*', allowEmptyArchive: false
    }
}
```
