"""Domain entities for analysis results."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from ..enumerators.analysis_status import AnalysisStatus
from .project import Project

@dataclass(frozen=True)
class ProjectAnalysisResult:
    """Result of CodeQL analysis for a single project."""
    
    project: Project
    status: AnalysisStatus
    output_files: List[Path] = field(default_factory=list)
    error_message: Optional[str] = None
    
    def is_successful(self) -> bool:
        """Check if analysis was successful."""
        return self.status == AnalysisStatus.COMPLETED and self.error_message is None

@dataclass(frozen=True)
class RepositoryAnalysisResult:
    """Complete result of repository analysis including all projects."""
    
    failed_projects: List[ProjectAnalysisResult] 
    successful_projects: List[ProjectAnalysisResult] 
    error_message: Optional[str] = None
    
    def is_successful(self) -> bool:
        """Check if repository analysis was successful."""
        return (
            self.error_message is None and
            len(self.failed_projects) == 0
        )
    
    def get_sarif_files(self) -> List[Path]:
        """Get all SARIF output files."""
        sarif_files = []
        for result in self.successful_projects:
            for output_file in result.output_files:
                if str(output_file).endswith(".sarif"):
                    sarif_files.append(output_file)
        return sarif_files
