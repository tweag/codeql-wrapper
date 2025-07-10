---
sidebar_position: 5
---

# API Reference

Python API documentation for using CodeQL Wrapper programmatically.

## Overview

CodeQL Wrapper provides a comprehensive Python API for integrating CodeQL analysis into your applications. The main entry points are the `CodeQLAnalysisUseCase` and `SarifUploadUseCase` classes, following clean architecture principles with domain entities and use cases.

## Installation

Import the necessary classes and utilities:

```python
from codeql_wrapper.domain.use_cases.codeql_analysis_use_case import CodeQLAnalysisUseCase
from codeql_wrapper.domain.use_cases.sarif_upload_use_case import SarifUploadUseCase
from codeql_wrapper.domain.entities.codeql_analysis import (
    CodeQLAnalysisRequest,
    CodeQLLanguage,
    AnalysisStatus,
    SarifUploadRequest,
    ProjectInfo,
    RepositoryAnalysisSummary,
    CodeQLAnalysisResult,
    CodeQLInstallationInfo
)
from codeql_wrapper.infrastructure.logger import get_logger, configure_logging
```

## Quick Start

```python
import logging
from pathlib import Path
from codeql_wrapper.domain.use_cases.codeql_analysis_use_case import CodeQLAnalysisUseCase
from codeql_wrapper.domain.entities.codeql_analysis import CodeQLAnalysisRequest
from codeql_wrapper.infrastructure.logger import get_logger, configure_logging

# Configure logging
configure_logging(verbose=True)
logger = get_logger(__name__)

# Create use case instance
analysis_use_case = CodeQLAnalysisUseCase(logger)

# Create analysis request with automatic path validation
request = CodeQLAnalysisRequest(
    repository_path=Path("/path/to/repository"),
    output_directory=Path("/path/to/output"),
    verbose=True,
    monorepo=False,  # Set to True for monorepo analysis
    force_install=False  # Set to True to force CodeQL reinstallation
)

# Execute analysis
try:
    result = analysis_use_case.execute(request)
    
    # The result contains comprehensive information
    print(f"Analysis completed: {result.success_rate:.2%} success rate")
    print(f"Total findings: {result.total_findings}")
    print(f"Successful analyses: {result.successful_analyses}")
    print(f"Failed analyses: {result.failed_analyses}")
    print(f"Projects detected: {len(result.detected_projects)}")
    
    # Check individual project results
    for analysis_result in result.analysis_results:
        project = analysis_result.project_info
        print(f"Project: {project.name} ({project.primary_language.value if project.primary_language else 'unknown'})")
        print(f"  Status: {analysis_result.status.value}")
        print(f"  Findings: {analysis_result.findings_count}")
        
except ValueError as e:
    # Validation errors (e.g., path doesn't exist)
    logger.error(f"Request validation failed: {e}")
except Exception as e:
    # Analysis execution errors
    logger.error(f"Analysis failed: {e}")
```

## Core Classes

### CodeQLAnalysisUseCase

The main orchestrator for CodeQL analysis operations. This class handles both single repository and monorepo analysis workflows.

```python
class CodeQLAnalysisUseCase:
    DEFAULT_MAX_WORKERS: int = 10  # Maximum parallel processes for monorepo analysis
    
    def __init__(self, logger: Any) -> None:
        """Initialize the use case with dependencies."""
        
    def execute(self, request: CodeQLAnalysisRequest) -> RepositoryAnalysisSummary:
        """
        Execute CodeQL analysis on a repository or monorepo.
        
        Automatically detects whether to run single repository or monorepo analysis
        based on the request.monorepo flag and presence of .codeql.json configuration.
        
        Args:
            request: CodeQL analysis request with configuration
            
        Returns:
            RepositoryAnalysisSummary with comprehensive analysis results
            
        Raises:
            ValueError: If request validation fails
            Exception: If CodeQL installation or analysis fails
        """
```

#### Key Methods

- `execute(request)` - Main entry point for analysis
- `_verify_codeql_installation(force_install)` - Ensures CodeQL CLI is installed
- `_detect_projects(repository_path)` - Discovers projects in repository
- `_filter_projects_by_language(projects, languages)` - Filters projects by target languages
- `_analyze_project(project, request)` - Analyzes a single project
- `_execute_monorepo_analysis(request, config_data)` - Handles monorepo analysis with parallel processing

### CodeQLAnalysisRequest

Represents a request for CodeQL analysis with comprehensive configuration options.

```python
@dataclass
class CodeQLAnalysisRequest:
    repository_path: Path
    force_install: bool = False
    target_languages: Optional[Set[CodeQLLanguage]] = None
    verbose: bool = False
    output_directory: Optional[Path] = None
    monorepo: bool = False
    build_mode: Optional[str] = None
    build_script: Optional[str] = None
    queries: Optional[List[str]] = None
```

The constructor automatically validates the repository path and raises `ValueError` if the path doesn't exist or isn't a directory.

#### Properties

- `repository_path: Path` - **Required**. Repository path to analyze
- `force_install: bool` - Force CodeQL CLI reinstallation (default: False)
- `target_languages: Optional[Set[CodeQLLanguage]]` - Languages to analyze (None for auto-detection)
- `verbose: bool` - Enable verbose logging (default: False)
- `output_directory: Optional[Path]` - Output directory for results (None for default)
- `monorepo: bool` - Enable monorepo mode (default: False)
- `build_mode: Optional[str]` - Build mode for compiled languages ('manual', 'autobuild', 'none')
- `build_script: Optional[str]` - Custom build script path
- `queries: Optional[List[str]]` - Specific query suites to execute

### RepositoryAnalysisSummary

Contains comprehensive results and statistics for a repository analysis.

```python
@dataclass
class RepositoryAnalysisSummary:
    repository_path: Path
    detected_projects: List[ProjectInfo]
    analysis_results: List[CodeQLAnalysisResult]
    total_findings: int = 0
    successful_analyses: int = 0
    failed_analyses: int = 0
    error: Optional[str] = None
```

#### Properties

- `repository_path: Path` - Path to the analyzed repository
- `detected_projects: List[ProjectInfo]` - List of detected projects in the repository
- `analysis_results: List[CodeQLAnalysisResult]` - Detailed results for each analyzed project
- `total_findings: int` - **Auto-calculated**. Total security findings across all projects
- `successful_analyses: int` - **Auto-calculated**. Number of successful analyses
- `failed_analyses: int` - **Auto-calculated**. Number of failed analyses
- `error: Optional[str]` - Overall error message if repository analysis failed
- `success_rate: float` - **Property**. Success rate as a decimal (0.0 to 1.0)

### CodeQLAnalysisResult

Results for a single project analysis with detailed information and status.

```python
@dataclass
class CodeQLAnalysisResult:
    project_info: ProjectInfo
    status: AnalysisStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    output_files: Optional[List[Path]] = None
    error_message: Optional[str] = None
    findings_count: int = 0
```

#### Properties

- `project_info: ProjectInfo` - Information about the analyzed project
- `status: AnalysisStatus` - Current analysis status (PENDING, RUNNING, COMPLETED, FAILED, SKIPPED)
- `start_time: datetime` - When the analysis started
- `end_time: Optional[datetime]` - When the analysis completed (None if still running)
- `output_files: Optional[List[Path]]` - Generated output files (SARIF, logs, etc.)
- `error_message: Optional[str]` - Error details if analysis failed
- `findings_count: int` - Number of security findings discovered
- `duration: Optional[float]` - **Property**. Analysis duration in seconds
- `is_successful: bool` - **Property**. True if analysis completed successfully

### ProjectInfo

Information about a detected project with validation and metadata.

```python
@dataclass(frozen=True)
class ProjectInfo:
    path: Path
    name: str
    languages: Set[CodeQLLanguage]
    primary_language: Optional[CodeQLLanguage] = None
    framework: Optional[str] = None
    build_files: Optional[List[str]] = None
```

#### Properties

- `path: Path` - **Required**. Path to the project directory
- `name: str` - **Required**. Project name (usually directory name)
- `languages: Set[CodeQLLanguage]` - **Required**. Set of detected programming languages
- `primary_language: Optional[CodeQLLanguage]` - Main language (highest priority)
- `framework: Optional[str]` - Detected framework (e.g., "Spring Boot", "Django")
- `build_files: Optional[List[str]]` - Detected build files (e.g., "pom.xml", "package.json")

#### Validation

- Project path must exist
- Project name cannot be empty
- At least one language must be detected
- Uses `@dataclass(frozen=True)` for immutability

### CodeQLInstallationInfo

Information about the CodeQL CLI installation status.

```python
@dataclass
class CodeQLInstallationInfo:
    is_installed: bool
    version: Optional[str] = None
    path: Optional[Path] = None
    error_message: Optional[str] = None
```

#### Properties

- `is_installed: bool` - Whether CodeQL CLI is installed
- `version: Optional[str]` - Installed CodeQL version
- `path: Optional[Path]` - Path to CodeQL binary
- `error_message: Optional[str]` - Error details if installation check failed
- `is_valid: bool` - **Property**. True if installation is complete and usable

## Enumerations

### CodeQLLanguage

Supported programming languages for CodeQL analysis.

```python
class CodeQLLanguage(Enum):
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    PYTHON = "python"
    JAVA = "java"
    CSHARP = "csharp"
    CPP = "cpp"
    GO = "go"
    RUBY = "ruby"
    SWIFT = "swift"
    KOTLIN = "kotlin"
    ACTIONS = "actions"    # GitHub Actions workflows
```

### AnalysisStatus

Current status of a CodeQL analysis operation.

```python
class AnalysisStatus(Enum):
    PENDING = "pending"    # Analysis queued but not started
    RUNNING = "running"    # Analysis in progress
    COMPLETED = "completed" # Analysis finished successfully
    FAILED = "failed"      # Analysis failed with errors
    SKIPPED = "skipped"    # Analysis was skipped (e.g., no supported files)
```

## API Reference Summary

### Main Classes Overview

| Class | Purpose | Key Methods & Properties |
|-------|---------|--------------------------|
| `CodeQLAnalysisUseCase` | Main analysis orchestrator | `execute(request)`, `DEFAULT_MAX_WORKERS=10` |
| `SarifUploadUseCase` | SARIF upload to GitHub Code Scanning | `execute(upload_request)`, `UPLOAD_TIMEOUT_SECONDS=300` |
| `CodeQLAnalysisRequest` | Analysis configuration with validation | All configuration properties, automatic `__post_init__` validation |
| `RepositoryAnalysisSummary` | Analysis results container | `success_rate`, auto-calculated statistics |
| `CodeQLAnalysisResult` | Individual project results | `duration`, `is_successful`, status tracking |
| `ProjectInfo` | Project metadata (immutable) | Language detection, framework identification |
| `CodeQLInstallationInfo` | CodeQL CLI installation status | `is_valid` property for installation verification |

### Key Features Implemented

- **Automatic CodeQL Installation**: Downloads and installs CodeQL CLI if not present
- **Language Detection**: Automatically detects supported languages in repositories
- **Monorepo Support**: Handles complex monorepo structures with `.codeql.json` configuration
- **Parallel Processing**: Concurrent analysis of multiple projects (up to 10 workers)
- **SARIF Upload**: Direct integration with GitHub Code Scanning via CodeQL CLI
- **Comprehensive Error Handling**: Detailed error reporting and status tracking
- **Logging Infrastructure**: Custom `ShortNameFormatter` for cleaner output
- **Path Validation**: Automatic validation in dataclass constructors
- **Build Mode Support**: Manual, autobuild, and none build modes for different project types

### Development Best Practices

1. **Always configure logging** before creating use cases for proper monitoring
2. **Use Path objects** for all file system operations for cross-platform compatibility
3. **Handle exceptions** appropriately with specific catch blocks for different error types
4. **Validate inputs** using the built-in validation or custom validation functions
5. **Check analysis status** before processing results to handle failures gracefully
6. **Use monorepo mode** for repositories with multiple projects for optimal performance
7. **Leverage automatic language detection** unless specific filtering is required
8. **Monitor resource usage** when analyzing large repositories or monorepos
9. **Implement proper cleanup** of temporary files and resources
10. **Use structured logging** for CI/CD integration and debugging

### Quick Integration Template

```python
# Minimal integration template
from pathlib import Path
from codeql_wrapper.domain.use_cases.codeql_analysis_use_case import CodeQLAnalysisUseCase
from codeql_wrapper.domain.entities.codeql_analysis import CodeQLAnalysisRequest
from codeql_wrapper.infrastructure.logger import get_logger, configure_logging

def analyze_repository(repo_path: str, output_dir: str = None) -> bool:
    """Simple repository analysis with error handling."""
    configure_logging(verbose=False)
    logger = get_logger(__name__)
    
    try:
        use_case = CodeQLAnalysisUseCase(logger)
        request = CodeQLAnalysisRequest(
            repository_path=Path(repo_path),
            output_directory=Path(output_dir) if output_dir else None
        )
        result = use_case.execute(request)
        
        print(f"Analysis complete: {result.total_findings} findings")
        print(f"Success rate: {result.success_rate:.2%}")
        return result.success_rate > 0.5  # Consider >50% success as acceptable
        
    except ValueError as e:
        print(f"Configuration error: {e}")
        return False
    except Exception as e:
        print(f"Analysis error: {e}")
        return False

# Usage
success = analyze_repository("./my-project", "./output")
```

### Common Integration Patterns

- **CI/CD Pipeline**: Use with exit codes for build success/failure determination
- **Security Scanning**: Integrate with existing security tools via SARIF output
- **Code Quality Gates**: Use findings count and success rate for quality metrics
- **Monorepo Workflows**: Configure per-project analysis with `.codeql.json`
- **Enterprise Security**: Batch analysis with centralized reporting and SARIF upload

For detailed usage examples and integration guides, see the [CLI Usage Guide](./cli-usage) and [CI/CD Integration](./cicd-integration) documentation.

## Advanced Usage

### Monorepo Analysis with Custom Configuration

The CodeQL Wrapper supports complex monorepo analysis using a `.codeql.json` configuration file. When this file is present in the repository root, it enables per-project configuration.

```python
# Example .codeql.json configuration
config = {
    "projects": [
        {
            "path": "./backend/api-service",
            "build-mode": "manual",
            "build-script": "./scripts/build-api.sh",
            "queries": ["security-extended"]
        },
        {
            "path": "./frontend/web-app",
            "build-mode": "none",
            "queries": ["security-extended", "code-scanning"]
        }
    ]
}

# Analyze a monorepo with specific build configuration
request = CodeQLAnalysisRequest(
    repository_path=Path("/path/to/monorepo"),
    monorepo=True,
    output_directory=Path("/path/to/output"),
    build_mode="manual",  # Can be overridden by .codeql.json
    build_script="./scripts/build.sh",  # Can be overridden by .codeql.json
    queries=["security-extended", "code-scanning"]  # Can be overridden by .codeql.json
)

result = analysis_use_case.execute(request)

# The analysis will automatically use parallel processing for multiple projects
# Maximum parallel workers is controlled by DEFAULT_MAX_WORKERS (10)

# Process results for each project
for analysis_result in result.analysis_results:
    project = analysis_result.project_info
    print(f"Project: {project.name}")
    print(f"Languages: {[lang.value for lang in project.languages]}")
    print(f"Framework: {project.framework}")
    print(f"Build files: {project.build_files}")
    print(f"Findings: {analysis_result.findings_count}")
    print(f"Status: {analysis_result.status.value}")
    print(f"Duration: {analysis_result.duration:.2f}s" if analysis_result.duration else "N/A")
    print(f"Success: {analysis_result.is_successful}")
    print("---")
```

#### Monorepo Configuration Options

- **Auto-discovery mode**: When `monorepo=True` and no `.codeql.json` exists, automatically analyzes all subdirectories
- **Configuration mode**: When `.codeql.json` exists, uses project-specific settings for build modes, scripts, and queries
- **Parallel processing**: Automatically runs analysis on multiple projects concurrently (up to `DEFAULT_MAX_WORKERS=10`)
- **Per-project settings**: Each project can have different build modes, scripts, and query suites

### Language Filtering and Targeting

```python
from codeql_wrapper.domain.entities.codeql_analysis import CodeQLLanguage

# Define target languages using the enum
target_languages = {
    CodeQLLanguage.PYTHON, 
    CodeQLLanguage.JAVASCRIPT,
    CodeQLLanguage.TYPESCRIPT
}

request = CodeQLAnalysisRequest(
    repository_path=Path("/path/to/repository"),
    target_languages=target_languages,
    verbose=True  # Enable detailed logging
)

result = analysis_use_case.execute(request)

# Check which languages were actually analyzed
for analysis_result in result.analysis_results:
    detected_languages = analysis_result.project_info.languages
    analyzed_languages = detected_languages.intersection(target_languages)
    print(f"Requested: {[lang.value for lang in target_languages]}")
    print(f"Detected: {[lang.value for lang in detected_languages]}")
    print(f"Analyzed: {[lang.value for lang in analyzed_languages]}")

# Language mapping used by CLI (for reference)
CLI_LANGUAGE_MAPPING = {
    "javascript": CodeQLLanguage.JAVASCRIPT,
    "typescript": CodeQLLanguage.TYPESCRIPT,
    "python": CodeQLLanguage.PYTHON,
    "java": CodeQLLanguage.JAVA,
    "csharp": CodeQLLanguage.CSHARP,
    "cpp": CodeQLLanguage.CPP,
    "go": CodeQLLanguage.GO,
    "ruby": CodeQLLanguage.RUBY,
    "swift": CodeQLLanguage.SWIFT,
    "actions": CodeQLLanguage.ACTIONS,
}

# Convert CLI language strings to enums
def parse_languages_from_cli(language_string: str) -> Set[CodeQLLanguage]:
    """Convert comma-separated language string to CodeQLLanguage set."""
    if not language_string:
        return None
    
    languages = set()
    for lang in language_string.split(','):
        lang = lang.strip().lower()
        if lang in CLI_LANGUAGE_MAPPING:
            languages.add(CLI_LANGUAGE_MAPPING[lang])
    return languages
```

### Handling Large Repositories with Parallel Processing

```python
# The CodeQLAnalysisUseCase automatically handles parallel processing
# You can monitor progress through logging

import logging
from codeql_wrapper.infrastructure.logger import configure_logging

# Enable detailed logging to see parallel processing
configure_logging(verbose=True)
logger = get_logger(__name__, level=logging.DEBUG)

analysis_use_case = CodeQLAnalysisUseCase(logger)

# For large monorepos, the analysis will automatically:
# 1. Detect all projects
# 2. Run analyses in parallel (up to DEFAULT_MAX_WORKERS=10)
# 3. Aggregate results

request = CodeQLAnalysisRequest(
    repository_path=Path("/path/to/large/monorepo"),
    monorepo=True
)

result = analysis_use_case.execute(request)

print(f"Processed {len(result.detected_projects)} projects")
print(f"Parallel analyses: {len(result.analysis_results)}")
print(f"Success rate: {result.success_rate:.2%}")
```

### Custom Output Processing and SARIF Handling

```python
import json
from pathlib import Path

# Analyze and process SARIF files with custom logic
result = analysis_use_case.execute(request)

sarif_files = []
for analysis_result in result.analysis_results:
    if analysis_result.output_files:
        for output_file in analysis_result.output_files:
            if output_file.suffix == '.sarif':
                sarif_files.append(output_file)
                
                # Custom SARIF processing
                with open(output_file, 'r', encoding='utf-8') as f:
                    sarif_data = json.load(f)
                    
                # Extract findings details
                for run in sarif_data.get('runs', []):
                    results = run.get('results', [])
                    print(f"File: {output_file.name}")
                    print(f"Tool: {run.get('tool', {}).get('driver', {}).get('name', 'Unknown')}")
                    print(f"Results: {len(results)}")
                    
                    # Process each finding
                    for result_item in results:
                        rule_id = result_item.get('ruleId', 'Unknown')
                        message = result_item.get('message', {}).get('text', 'No message')
                        level = result_item.get('level', 'note')
                        print(f"  - {rule_id} ({level}): {message}")

print(f"Total SARIF files generated: {len(sarif_files)}")
```

## SARIF Upload API

### Complete SARIF Upload Example

```python
from codeql_wrapper.domain.use_cases.sarif_upload_use_case import SarifUploadUseCase
from codeql_wrapper.domain.entities.codeql_analysis import SarifUploadRequest

# Create upload use case
upload_use_case = SarifUploadUseCase(logger)

# Create upload request for multiple files
upload_request = SarifUploadRequest(
    sarif_files=[
        Path("/path/to/results1.sarif"),
        Path("/path/to/results2.sarif")
    ],
    repository="owner/repo-name",
    commit_sha="abc123def456",
    github_token="ghp_your_token_here",
    ref="refs/heads/main"  # Optional - defaults to refs/heads/main
)

# Upload SARIF files
try:
    upload_result = upload_use_case.execute(upload_request)
    
    if upload_result.success:
        print(f"Successfully uploaded {upload_result.successful_uploads}/{upload_result.total_files} files")
        print(f"Success rate: {upload_result.success_rate:.2%}")
    else:
        print(f"Upload failed: {upload_result.failed_uploads} failures")
        if upload_result.errors:
            for error in upload_result.errors:
                print(f"  Error: {error}")
                
except ValueError as e:
    print(f"Invalid upload request: {e}")
except Exception as e:
    print(f"Upload error: {e}")
```

### SarifUploadRequest

Request configuration for uploading SARIF files.

```python
@dataclass
class SarifUploadRequest:
    sarif_files: List[Path]
    repository: str
    commit_sha: str
    github_token: str
    ref: Optional[str] = None
```

#### Properties

- `sarif_files: List[Path]` - **Required**. List of SARIF files to upload
- `repository: str` - **Required**. Repository in 'owner/name' format
- `commit_sha: str` - **Required**. Full commit SHA (40 characters)
- `github_token: str` - **Required**. GitHub personal access token
- `ref: Optional[str]` - Git reference (default: refs/heads/main)

#### Validation

The constructor automatically validates:
- At least one SARIF file must be provided
- All SARIF files must exist and have `.sarif` extension
- Repository must be in `owner/name` format
- Commit SHA and GitHub token are required

### SarifUploadResult

Result of the SARIF upload operation.

```python
@dataclass
class SarifUploadResult:
    success: bool
    successful_uploads: int
    failed_uploads: int
    total_files: int
    errors: Optional[List[str]] = None
```

#### Properties

- `success: bool` - Overall upload success (True if all files uploaded successfully)
- `successful_uploads: int` - Number of successful uploads
- `failed_uploads: int` - Number of failed uploads
- `total_files: int` - Total files attempted
- `errors: Optional[List[str]]` - List of error messages if any uploads failed
- `success_rate: float` - **Property**. Upload success rate (0.0 to 1.0)

## Error Handling

### Exception Types and Handling Strategies

```python
from codeql_wrapper.domain.entities.codeql_analysis import AnalysisStatus

try:
    result = analysis_use_case.execute(request)
    
    # Check overall analysis result
    if result.error:
        print(f"Repository-level error: {result.error}")
        return
    
    # Process individual project results
    successful_projects = []
    failed_projects = []
    
    for analysis_result in result.analysis_results:
        project_name = analysis_result.project_info.name
        
        if analysis_result.status == AnalysisStatus.COMPLETED and analysis_result.is_successful:
            successful_projects.append(project_name)
            print(f"{project_name}: {analysis_result.findings_count} findings")
            
        elif analysis_result.status == AnalysisStatus.FAILED:
            failed_projects.append(project_name)
            print(f"{project_name}: {analysis_result.error_message}")
            
        elif analysis_result.status == AnalysisStatus.SKIPPED:
            print(f"{project_name}: Skipped (no supported files)")
            
        elif analysis_result.status == AnalysisStatus.RUNNING:
            print(f"{project_name}: Still running (unexpected)")
    
    # Summary
    print(f"\nSummary:")
    print(f"  Successful: {len(successful_projects)}")
    print(f"  Failed: {len(failed_projects)}")
    print(f"  Success rate: {result.success_rate:.2%}")

except ValueError as e:
    # Input validation errors
    print(f"Invalid input: {e}")
    print("Check repository path, output directory, and other parameters")
    
except FileNotFoundError as e:
    # File/directory not found
    print(f"File not found: {e}")
    print("Ensure repository path exists and is accessible")
    
except PermissionError as e:
    # Permission issues
    print(f"Permission denied: {e}")
    print("Check read/write permissions for repository and output directories")
    
except Exception as e:
    # Unexpected errors
    print(f"Unexpected error: {e}")
    logger.exception("Full error details:")
```

### Validation and Pre-flight Checks

The CodeQL Wrapper performs automatic validation in the dataclass constructors. Here's how to implement additional validation:

```python
def validate_analysis_request(request: CodeQLAnalysisRequest) -> List[str]:
    """Validate analysis request and return list of issues."""
    issues = []
    
    # Note: Basic path validation is already done in __post_init__
    # This function provides additional checks
    
    # Check repository accessibility
    try:
        # Test read access
        list(request.repository_path.iterdir())
    except PermissionError:
        issues.append(f"No read permission for repository: {request.repository_path}")
    except OSError as e:
        issues.append(f"Cannot access repository: {e}")
    
    # Check output directory
    if request.output_directory:
        if request.output_directory.exists() and not request.output_directory.is_dir():
            issues.append(f"Output path exists but is not a directory: {request.output_directory}")
        
        # Check write permissions
        try:
            request.output_directory.mkdir(parents=True, exist_ok=True)
            test_file = request.output_directory / ".write_test"
            test_file.touch()
            test_file.unlink()
        except (PermissionError, OSError) as e:
            issues.append(f"Cannot write to output directory: {e}")
    
    # Check language constraints
    if request.target_languages:
        valid_languages = set(CodeQLLanguage)
        invalid_languages = request.target_languages - valid_languages
        if invalid_languages:
            issues.append(f"Invalid languages specified: {invalid_languages}")
    
    # Check build script existence if specified
    if request.build_script:
        build_script_path = request.repository_path / request.build_script
        if not build_script_path.exists():
            issues.append(f"Build script not found: {build_script_path}")
        elif not build_script_path.is_file():
            issues.append(f"Build script path is not a file: {build_script_path}")
    
    return issues

# Usage with automatic validation
try:
    request = CodeQLAnalysisRequest(
        repository_path=Path("/path/to/repo"),
        output_directory=Path("/path/to/output")
    )
    
    # Additional validation
    validation_issues = validate_analysis_request(request)
    if validation_issues:
        print("Validation failed:")
        for issue in validation_issues:
            print(f"  - {issue}")
        sys.exit(1)
    else:
        result = analysis_use_case.execute(request)
        
except ValueError as e:
    # Catches validation errors from __post_init__
    print(f"Request validation failed: {e}")
    sys.exit(1)
```

## Logging Configuration

### Setting Up Comprehensive Logging

The CodeQL Wrapper uses a custom logging infrastructure with short name formatting for cleaner output.

```python
from codeql_wrapper.infrastructure.logger import get_logger, configure_logging
import logging

# Global logging configuration
configure_logging(verbose=True)  # Enables detailed output

# Create loggers for different components
main_logger = get_logger(__name__)
analysis_logger = get_logger("analysis", level=logging.DEBUG)

# Use with analysis components
analysis_use_case = CodeQLAnalysisUseCase(analysis_logger)
upload_use_case = SarifUploadUseCase(analysis_logger)

# The logging system uses a ShortNameFormatter that shows only 
# the class name instead of the full module path for cleaner output
```

### Available Logging Functions

```python
def get_logger(
    name: str, 
    level: Optional[int] = None, 
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Get a configured logger instance with optional custom formatting.
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level (if None, inherits from root logger)
        format_string: Custom format string
        
    Returns:
        Configured logger instance with ShortNameFormatter
    """

def configure_logging(verbose: bool = False) -> None:
    """
    Configure global logging settings.
    
    Args:
        verbose: Enable DEBUG level logging if True, INFO level if False
    """
```

### Logging Levels and Usage

- **DEBUG**: Detailed diagnostic information (verbose mode)
- **INFO**: General information about progress
- **WARNING**: Something unexpected happened but operation continues
- **ERROR**: Serious problem, operation may fail
- **CRITICAL**: Very serious error, program may abort
