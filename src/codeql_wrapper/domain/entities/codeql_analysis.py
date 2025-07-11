"""CodeQL analysis domain entities."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Set
from datetime import datetime


class CodeQLLanguage(Enum):
    """Supported CodeQL languages."""

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


class AnalysisStatus(Enum):
    """Status of CodeQL analysis."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class ProjectInfo:
    """Information about a detected project."""

    path: Path
    name: str
    languages: Set[CodeQLLanguage]
    primary_language: Optional[CodeQLLanguage] = None
    framework: Optional[str] = None
    build_files: Optional[List[str]] = None

    def __post_init__(self) -> None:
        """Validate project information."""
        if not self.path.exists():
            raise ValueError(f"Project path does not exist: {self.path}")

        if not self.name or not self.name.strip():
            raise ValueError("Project name cannot be empty")

        if not self.languages:
            raise ValueError("At least one language must be detected")


@dataclass
class CodeQLAnalysisRequest:
    """Request for CodeQL analysis."""

    repository_path: Path
    force_install: bool = False
    target_languages: Optional[Set[CodeQLLanguage]] = None
    verbose: bool = False
    output_directory: Optional[Path] = None
    monorepo: bool = False
    build_mode: Optional[str] = None
    build_script: Optional[str] = None
    queries: Optional[List[str]] = None
    max_workers: Optional[int] = None

    def __post_init__(self) -> None:
        """Validate analysis request."""
        if not self.repository_path.exists():
            raise ValueError(f"Repository path does not exist: {self.repository_path}")

        if not self.repository_path.is_dir():
            raise ValueError(
                f"Repository path must be a directory: {self.repository_path}"
            )


@dataclass
class CodeQLAnalysisResult:
    """Result of CodeQL analysis for a single project."""

    project_info: ProjectInfo
    status: AnalysisStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    output_files: Optional[List[Path]] = None
    error_message: Optional[str] = None
    findings_count: int = 0

    def __post_init__(self) -> None:
        """Initialize default values."""
        if self.output_files is None:
            object.__setattr__(self, "output_files", [])

    @property
    def duration(self) -> Optional[float]:
        """Calculate analysis duration in seconds."""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def is_successful(self) -> bool:
        """Check if analysis was successful."""
        return self.status == AnalysisStatus.COMPLETED and self.error_message is None


@dataclass
class CodeQLInstallationInfo:
    """Information about CodeQL CLI installation."""

    is_installed: bool
    version: Optional[str] = None
    path: Optional[Path] = None
    error_message: Optional[str] = None

    @property
    def is_valid(self) -> bool:
        """Check if CodeQL installation is valid and usable."""
        return self.is_installed and self.version is not None and self.path is not None


@dataclass
class RepositoryAnalysisSummary:
    """Summary of repository analysis results."""

    repository_path: Path
    detected_projects: List[ProjectInfo]
    analysis_results: List[CodeQLAnalysisResult]
    total_findings: int = 0
    successful_analyses: int = 0
    failed_analyses: int = 0
    error: Optional[str] = None

    def __post_init__(self) -> None:
        """Calculate summary statistics."""
        self.successful_analyses = sum(
            1 for result in self.analysis_results if result.is_successful
        )
        self.failed_analyses = len(self.analysis_results) - self.successful_analyses
        self.total_findings = sum(
            result.findings_count for result in self.analysis_results
        )

    @property
    def success_rate(self) -> float:
        """Calculate analysis success rate."""
        if not self.analysis_results:
            return 0.0
        return self.successful_analyses / len(self.analysis_results)


@dataclass
class SarifUploadRequest:
    """Request for uploading SARIF files to GitHub Code Scanning."""

    sarif_files: List[Path]
    repository: str  # Format: 'owner/name'
    commit_sha: str
    github_token: str
    ref: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate upload request."""
        if not self.sarif_files:
            raise ValueError("At least one SARIF file is required")

        for sarif_file in self.sarif_files:
            if not sarif_file.exists():
                raise ValueError(f"SARIF file does not exist: {sarif_file}")
            if sarif_file.suffix != ".sarif":
                raise ValueError(f"File is not a SARIF file: {sarif_file}")

        if "/" not in self.repository:
            raise ValueError("Repository must be in 'owner/name' format")

        if not self.commit_sha:
            raise ValueError("Commit SHA is required")

        if not self.github_token:
            raise ValueError("GitHub token is required")


@dataclass
class SarifUploadResult:
    """Result of SARIF upload operation."""

    success: bool
    successful_uploads: int
    failed_uploads: int
    total_files: int
    errors: Optional[List[str]] = None

    @property
    def success_rate(self) -> float:
        """Calculate upload success rate."""
        if self.total_files == 0:
            return 0.0
        return self.successful_uploads / self.total_files
