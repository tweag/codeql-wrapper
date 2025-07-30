***

## sidebar\_position: 5

# API Reference

Python API documentation for using CodeQL Wrapper programmatically.

## Overview

CodeQL Wrapper provides a Python API for integrating CodeQL analysis into your applications. The main entry points are the `CodeQLAnalysisUseCase` and `SarifUploadUseCase` classes.

## Installation

```python
from codeql_wrapper.domain.use_cases.codeql_analysis_use_case import CodeQLAnalysisUseCase
from codeql_wrapper.domain.entities.codeql_analysis import CodeQLAnalysisRequest
from codeql_wrapper.infrastructure.logger import get_logger
```

## Basic Usage

```python
import logging
from pathlib import Path
from codeql_wrapper.domain.use_cases.codeql_analysis_use_case import CodeQLAnalysisUseCase
from codeql_wrapper.domain.entities.codeql_analysis import CodeQLAnalysisRequest
from codeql_wrapper.infrastructure.logger import get_logger
from codeql_wrapper.infrastructure.git_utils import GitInfo

# Set up logging
logger = get_logger(__name__, level=logging.INFO)

# Create use case instance
analysis_use_case = CodeQLAnalysisUseCase(logger)

# Create analysis request
request = CodeQLAnalysisRequest(
    repository_path=Path("/path/to/repository"),
    git_info=GitInfo(working_dir=Path("/path/to/repository"), branch="main", commit_sha="abcdef12345"),
    output_directory=Path("/path/to/output"),
    verbose=True
)

# Execute analysis
try:
    result = analysis_use_case.execute(request)
    print(f"Analysis completed: {result.success_rate:.2%} success rate")
    print(f"Total findings: {result.total_findings}")
except Exception as e:
    print(f"Analysis failed: {e}")
```

## Core Classes

### CodeQLAnalysisRequest

Represents a request for CodeQL analysis.

```python
@dataclass
class CodeQLAnalysisRequest:
    repository_path: Path
    git_info: GitInfo
    force_install: bool = False
    target_languages: Optional[Set[CodeQLLanguage]] = None
    verbose: bool = False
    output_directory: Optional[Path] = None
    monorepo: bool = False
    build_mode: Optional[str] = None
    build_script: Optional[Path] = None
    queries: Optional[List[str]] = None
    max_workers: Optional[int] = None
    only_changed_files: bool = False
```

#### Properties

* `repository_path: Path` - Path to the repository to analyze.
* `git_info: GitInfo` - Git information for the repository (e.g., branch, commit SHA).
* `force_install: bool` - If `True`, forces reinstallation of CodeQL CLI even if already present. Defaults to `False`.
* `target_languages: Optional[Set[CodeQLLanguage]]` - A set of specific languages to analyze. If `None`, all detected languages will be analyzed.
* `verbose: bool` - If `True`, enables verbose logging for more detailed output. Defaults to `False`.
* `output_directory: Optional[Path]` - The directory where analysis results (SARIF files, databases) will be stored. If `None`, results are stored in a default location within the project directory.
* `monorepo: bool` - If `True`, treats the repository as a monorepo and attempts to detect multiple projects within it. Defaults to `False`.
* `build_mode: Optional[str]` - Specifies the build mode for compiled languages (e.g., "autobuild", "none").
* `build_script: Optional[Path]` - Path to a custom build script to be executed before analysis for compiled languages.
* `queries: Optional[List[str]]` - A list of CodeQL query suite paths or names to run. If `None`, default queries are used.
* `max_workers: Optional[int]` - The maximum number of parallel workers to use for analysis. If `None`, an optimal number is calculated based on system resources.
* `only_changed_files: bool` - If `True`, only analyzes projects that have changed files based on Git history. Defaults to `False`.

### RepositoryAnalysisSummary

Contains the aggregated results of a CodeQL analysis across all detected projects.

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

* `repository_path: Path` - The path to the repository that was analyzed.
* `detected_projects: List[ProjectInfo]` - A list of `ProjectInfo` objects representing all projects detected within the repository.
* `analysis_results: List[CodeQLAnalysisResult]` - A list of `CodeQLAnalysisResult` objects, each containing the results for a single project's analysis.
* `total_findings: int` - The total number of security findings across all successful analyses.
* `successful_analyses: int` - The count of analyses that completed successfully.
* `failed_analyses: int` - The count of analyses that failed.
* `error: Optional[str]` - An aggregated error message if any top-level error occurred during the analysis process.
* `success_rate: float` - The success rate of analyses (calculated as `successful_analyses / total_analyses`).

### CodeQLAnalysisResult

Results for a single project's CodeQL analysis.

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

* `project_info: ProjectInfo` - Information about the specific project that was analyzed.
* `status: AnalysisStatus` - The current status of the analysis (e.g., `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`).
* `start_time: datetime` - The timestamp when the analysis started.
* `end_time: Optional[datetime]` - The timestamp when the analysis ended. `None` if still running or failed early.
* `output_files: Optional[List[Path]]` - A list of paths to the output files generated by the analysis (e.g., SARIF files).
* `error_message: Optional[str]` - A detailed error message if the analysis failed for this specific project.
* `findings_count: int` - The number of security findings identified in this project's analysis.
* `duration: float` - The duration of the analysis in seconds (calculated from `start_time` and `end_time`).

### ProjectInfo

Information about a detected project within a repository.

```python
@dataclass
class ProjectInfo:
    repository_path: Path
    project_path: Path
    name: str
    framework: Optional[str] = None
    build_files: Optional[List[str]] = None
    build_script: Optional[Path] = None
    queries: Optional[List[str]] = None
    non_compiled_languages: Set[CodeQLLanguage] = field(default_factory=set)
    compiled_languages: Set[CodeQLLanguage] = field(default_factory=set)
    target_language: Optional[CodeQLLanguage] = None
    build_mode: Optional[str] = None
    log_color: Optional[str] = None
```

#### Properties

* `repository_path: Path` - The root path of the Git repository containing the project.
* `project_path: Path` - The absolute path to the project directory.
* `name: str` - A human-readable name for the project.
* `framework: Optional[str]` - Detected framework of the project (e.g., "React", "Spring").
* `build_files: Optional[List[str]]` - List of detected build-related files (e.g., `pom.xml`, `package.json`).
* `build_script: Optional[Path]` - Path to a detected build script for the project.
* `queries: Optional[List[str]]` - Specific CodeQL queries or query suites configured for this project.
* `non_compiled_languages: Set[CodeQLLanguage]` - Set of non-compiled languages detected in the project (e.g., Python, JavaScript).
* `compiled_languages: Set[CodeQLLanguage]` - Set of compiled languages detected in the project (e.g., Java, C#).
* `target_language: Optional[CodeQLLanguage]` - The primary language targeted for analysis if specified.
* `build_mode: Optional[str]` - The build mode used for the project (e.g., "autobuild", "none").
* `log_color: Optional[str]` - ANSI escape code for logging output color, used for distinguishing project logs.

### GitInfo

Information about the Git repository state.

```python
@dataclass
class GitInfo:
    working_dir: Path
    branch: str
    commit_sha: str
    remote_url: Optional[str] = None
    base_branch: Optional[str] = None
    base_commit_sha: Optional[str] = None
```

#### Properties

* `working_dir: Path` - The working directory of the Git repository.
* `branch: str` - The current branch name.
* `commit_sha: str` - The full SHA of the current commit.
* `remote_url: Optional[str]` - The URL of the remote Git repository.
* `base_branch: Optional[str]` - The base branch for pull request analysis.
* `base_commit_sha: Optional[str]` - The base commit SHA for pull request analysis.

## Enumerations

### CodeQLLanguage

Supported CodeQL languages:

```python
class CodeQLLanguage(Enum):
    RUST = "rust"
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
    ACTIONS = "actions"
```

### AnalysisStatus

Analysis status values:

```python
class AnalysisStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
```

## Advanced Usage

### Monorepo Analysis

```python
# Analyze a monorepo
request = CodeQLAnalysisRequest(
    repository_path=Path("/path/to/monorepo"),
    git_info=GitInfo(working_dir=Path("/path/to/monorepo"), branch="main", commit_sha="abcdef12345"),
    monorepo=True,
    output_directory=Path("/path/to/output")
)

result = analysis_use_case.execute(request)

# Process results for each project
for analysis_result in result.analysis_results:
    project = analysis_result.project_info
    print(f"Project: {project.name}")
    # Note: project.languages is now split into non_compiled_languages and compiled_languages
    print(f"Non-compiled Languages: {[lang.value for lang in project.non_compiled_languages]}")
    print(f"Compiled Languages: {[lang.value for lang in project.compiled_languages]}")
    print(f"Findings: {analysis_result.findings_count}")
    print(f"Status: {analysis_result.status.value}")
```

### Language Filtering

```python
from codeql_wrapper.domain.entities.codeql_analysis import CodeQLLanguage, CodeQLAnalysisRequest
from codeql_wrapper.infrastructure.git_utils import GitInfo

# Analyze only Python and JavaScript
target_languages = {CodeQLLanguage.PYTHON, CodeQLLanguage.JAVASCRIPT}

request = CodeQLAnalysisRequest(
    repository_path=Path("/path/to/repository"),
    git_info=GitInfo(working_dir=Path("/path/to/repository"), branch="main", commit_sha="abcdef12345"),
    target_languages=target_languages
)

result = analysis_use_case.execute(request)
```

### Custom Output Processing

```python
import json

# Analyze and process SARIF files
result = analysis_use_case.execute(request)

for analysis_result in result.analysis_results:
    if analysis_result.output_files:
        for output_file in analysis_result.output_files:
            if output_file.suffix == ".sarif":
                # Process SARIF file
                with open(output_file, "r") as f:
                    sarif_data = json.load(f)
                    # Custom processing...
```

## SARIF Upload

### SarifUploadUseCase

Upload SARIF files to GitHub Code Scanning:

```python
from codeql_wrapper.domain.use_cases.sarif_upload_use_case import SarifUploadUseCase
from codeql_wrapper.domain.entities.codeql_analysis import SarifUploadRequest
from pathlib import Path

# Create upload use case
upload_use_case = SarifUploadUseCase(logger)

# Create upload request
upload_request = SarifUploadRequest(
    sarif_files=[Path("/path/to/results1.sarif"), Path("/path/to/results2.sarif")], # Note: sarif_files is a list
    repository="owner/repo",
    commit_sha="abc123",
    ref="refs/heads/main",
    github_token="your_token"
)

# Upload SARIF
try:
    upload_result = upload_use_case.execute(upload_request)
    if upload_result.success:
        print("SARIF uploaded successfully")
    else:
        print(f"Upload failed: {upload_result.errors}")
except Exception as e:
    print(f"Upload error: {e}")
```

### SarifUploadResult

Result of SARIF upload operation.

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

* `success: bool` - `True` if all SARIF files were uploaded successfully, `False` otherwise.
* `successful_uploads: int` - The number of SARIF files successfully uploaded.
* `failed_uploads: int` - The number of SARIF files that failed to upload.
* `total_files: int` - The total number of SARIF files attempted to upload.
* `errors: Optional[List[str]]` - A list of error messages for failed uploads.
* `success_rate: float` - The success rate of the upload operation (calculated as `successful_uploads / total_files`).

## Error Handling

```python
from codeql_wrapper.domain.entities.codeql_analysis import AnalysisStatus

try:
    result = analysis_use_case.execute(request)
    
    # Check overall result
    if result.error:
        print(f"Analysis error: {result.error}")
    
    # Check individual results
    for analysis_result in result.analysis_results:
        if analysis_result.status == AnalysisStatus.FAILED:
            print(f"Failed: {analysis_result.project_info.name}")
            print(f"Error: {analysis_result.error_message}")
        elif analysis_result.status == AnalysisStatus.COMPLETED:
            print(f"Success: {analysis_result.project_info.name}")
            print(f"Findings: {analysis_result.findings_count}")

except ValueError as e:
    print(f"Invalid input: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Logging

### Custom Logger Setup

```python
from codeql_wrapper.infrastructure.logger import get_logger, configure_logging
import logging

# Configure global logging
configure_logging(verbose=True)

# Get logger for your module
logger = get_logger(__name__, level=logging.DEBUG)

# Use with analysis
analysis_use_case = CodeQLAnalysisUseCase(logger)
```

## Examples

### Complete Analysis Workflow

```python
#!/usr/bin/env python3
"""
Complete CodeQL analysis workflow example
"""
import json
import logging
from pathlib import Path
from typing import List

from codeql_wrapper.domain.use_cases.codeql_analysis_use_case import CodeQLAnalysisUseCase
from codeql_wrapper.domain.entities.codeql_analysis import (
    CodeQLAnalysisRequest,
    CodeQLLanguage,
    AnalysisStatus
)
from codeql_wrapper.infrastructure.logger import get_logger, configure_logging
from codeql_wrapper.infrastructure.git_utils import GitInfo

def analyze_repository(repo_path: str, output_dir: str) -> None:
    """Analyze a repository and generate report."""
    
    # Configure logging
    configure_logging(verbose=True)
    logger = get_logger(__name__)
    
    # Create analysis request
    # Note: GitInfo is now a required parameter
    request = CodeQLAnalysisRequest(
        repository_path=Path(repo_path),
        git_info=GitInfo(working_dir=Path(repo_path), branch="main", commit_sha="abcdef12345"), # Example GitInfo
        output_directory=Path(output_dir),
        verbose=True
    )
    
    # Create and execute analysis
    analysis_use_case = CodeQLAnalysisUseCase(logger)
    
    try:
        result = analysis_use_case.execute(request)
        
        # Generate summary report
        report = {
            "repository": str(result.repository_path),
            "total_projects": len(result.detected_projects),
            "total_analyses": len(result.analysis_results),
            "successful_analyses": result.successful_analyses,
            "success_rate": result.success_rate,
            "total_findings": result.total_findings,
            "projects": []
        }
        
        # Add project details
        for analysis_result in result.analysis_results:
            project_info = {
                "name": analysis_result.project_info.name,
                "path": str(analysis_result.project_info.project_path),
                "non_compiled_languages": [lang.value for lang in analysis_result.project_info.non_compiled_languages],
                "compiled_languages": [lang.value for lang in analysis_result.project_info.compiled_languages],
                "status": analysis_result.status.value,
                "findings": analysis_result.findings_count,
                "duration": analysis_result.duration
            }
            
            if analysis_result.error_message:
                project_info["error"] = analysis_result.error_message
                
            if analysis_result.output_files:
                project_info["output_files"] = [str(f) for f in analysis_result.output_files]
            
            report["projects"].append(project_info)
        
        # Save report
        report_file = Path(output_dir) / "analysis-report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"Analysis completed: {result.success_rate:.2%} success rate")
        print(f"Report saved to: {report_file}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python analyze.py <repo_path> <output_dir>")
        sys.exit(1)
    
    analyze_repository(sys.argv[1], sys.argv[2])
```
