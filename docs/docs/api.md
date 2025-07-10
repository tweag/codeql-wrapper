---
sidebar_position: 5
---

# API Reference

Python API documentation for using CodeQL Wrapper programmatically.

## Overview

CodeQL Wrapper provides a Python API for integrating CodeQL analysis into your applications. The main entry point is the `CodeQLAnalysisUseCase` class.

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

# Set up logging
logger = get_logger(__name__, level=logging.INFO)

# Create use case instance
analysis_use_case = CodeQLAnalysisUseCase(logger)

# Create analysis request
request = CodeQLAnalysisRequest(
    repository_path=Path("/path/to/repository"),
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
class CodeQLAnalysisRequest:
    def __init__(
        self,
        repository_path: Path,
        target_languages: Optional[Set[CodeQLLanguage]] = None,
        output_directory: Optional[Path] = None,
        verbose: bool = False,
        force_install: bool = False,
        monorepo: bool = False
    ):
        """
        Args:
            repository_path: Path to the repository to analyze
            target_languages: Set of languages to analyze (None for all)
            output_directory: Directory to store results
            verbose: Enable verbose logging
            force_install: Force CodeQL reinstallation
            monorepo: Treat as monorepo
        """
```

#### Properties

- `repository_path: Path` - Repository path to analyze
- `target_languages: Optional[Set[CodeQLLanguage]]` - Languages to analyze
- `output_directory: Optional[Path]` - Output directory for results
- `verbose: bool` - Verbose logging flag
- `force_install: bool` - Force CodeQL installation
- `monorepo: bool` - Monorepo analysis flag

### RepositoryAnalysisSummary

Contains the results of a CodeQL analysis.

```python
@dataclass
class RepositoryAnalysisSummary:
    repository_path: Path
    detected_projects: List[ProjectInfo]
    analysis_results: List[CodeQLAnalysisResult]
    error: Optional[str] = None
```

#### Properties

- `repository_path: Path` - Repository that was analyzed
- `detected_projects: List[ProjectInfo]` - Detected projects
- `analysis_results: List[CodeQLAnalysisResult]` - Analysis results
- `error: Optional[str]` - Error message if analysis failed
- `total_findings: int` - Total security findings
- `success_rate: float` - Success rate (0.0 to 1.0)
- `successful_analyses: int` - Number of successful analyses

### CodeQLAnalysisResult

Results for a single project analysis.

```python
@dataclass
class CodeQLAnalysisResult:
    project_info: ProjectInfo
    status: AnalysisStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    findings_count: int = 0
    output_files: Optional[List[Path]] = None
    error_message: Optional[str] = None
```

#### Properties

- `project_info: ProjectInfo` - Project information
- `status: AnalysisStatus` - Analysis status
- `start_time: datetime` - Analysis start time
- `end_time: Optional[datetime]` - Analysis end time
- `findings_count: int` - Number of findings
- `output_files: Optional[List[Path]]` - Generated output files
- `error_message: Optional[str]` - Error message if failed
- `duration: float` - Analysis duration in seconds

### ProjectInfo

Information about a detected project.

```python
@dataclass
class ProjectInfo:
    path: Path
    name: str
    languages: Set[CodeQLLanguage]
    primary_language: Optional[CodeQLLanguage] = None
```

## Enumerations

### CodeQLLanguage

Supported CodeQL languages:

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
```

## Advanced Usage

### Monorepo Analysis

```python
# Analyze a monorepo
request = CodeQLAnalysisRequest(
    repository_path=Path("/path/to/monorepo"),
    monorepo=True,
    output_directory=Path("/path/to/output")
)

result = analysis_use_case.execute(request)

# Process results for each project
for analysis_result in result.analysis_results:
    project = analysis_result.project_info
    print(f"Project: {project.name}")
    print(f"Languages: {[lang.value for lang in project.languages]}")
    print(f"Findings: {analysis_result.findings_count}")
    print(f"Status: {analysis_result.status.value}")
```

### Language Filtering

```python
from codeql_wrapper.domain.entities.codeql_analysis import CodeQLLanguage

# Analyze only Python and JavaScript
target_languages = {CodeQLLanguage.PYTHON, CodeQLLanguage.JAVASCRIPT}

request = CodeQLAnalysisRequest(
    repository_path=Path("/path/to/repository"),
    target_languages=target_languages
)

result = analysis_use_case.execute(request)
```

### Custom Output Processing

```python
# Analyze and process SARIF files
result = analysis_use_case.execute(request)

for analysis_result in result.analysis_results:
    if analysis_result.output_files:
        for output_file in analysis_result.output_files:
            if output_file.suffix == '.sarif':
                # Process SARIF file
                with open(output_file, 'r') as f:
                    sarif_data = json.load(f)
                    # Custom processing...
```

## SARIF Upload

### SarifUploadUseCase

Upload SARIF files to GitHub Code Scanning:

```python
from codeql_wrapper.domain.use_cases.sarif_upload_use_case import SarifUploadUseCase
from codeql_wrapper.domain.entities.codeql_analysis import SarifUploadRequest

# Create upload use case
upload_use_case = SarifUploadUseCase(logger)

# Create upload request
upload_request = SarifUploadRequest(
    sarif_file=Path("/path/to/results.sarif"),
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
        print(f"Upload failed: {upload_result.error}")
except Exception as e:
    print(f"Upload error: {e}")
```

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

def analyze_repository(repo_path: str, output_dir: str) -> None:
    """Analyze a repository and generate report."""
    
    # Configure logging
    configure_logging(verbose=True)
    logger = get_logger(__name__)
    
    # Create analysis request
    request = CodeQLAnalysisRequest(
        repository_path=Path(repo_path),
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
                "path": str(analysis_result.project_info.path),
                "languages": [lang.value for lang in analysis_result.project_info.languages],
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
        with open(report_file, 'w') as f:
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
