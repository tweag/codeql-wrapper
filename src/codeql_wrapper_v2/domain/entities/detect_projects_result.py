"""Result entities for project detection operations."""

from dataclasses import dataclass
from typing import List, Optional

from ..entities.project import Project
from ..entities.repository import Repository


@dataclass(frozen=True)
class DetectProjectsResult:
    """Result of project detection operation."""
    
    repository: Repository
    detected_projects: List[Project]
    is_monorepo: bool
    config_file_used: Optional[str] = None
    error_message: Optional[str] = None
    
    def is_successful(self) -> bool:
        """Check if detection was successful."""
        return self.error_message is None
    
    def has_projects(self) -> bool:
        """Check if any projects were detected."""
        return len(self.detected_projects) > 0
    
    def get_project_count(self) -> int:
        """Get the number of detected projects."""
        return len(self.detected_projects)
    
    def get_projects_by_language(self, language_identifier: str) -> List[Project]:
        """Get projects that contain a specific language."""
        return [
            project for project in self.detected_projects
            if language_identifier in project.get_codeql_languages()
        ]
    
    def get_project_names(self) -> List[str]:
        """Get a list of all project names."""
        return [project.name for project in self.detected_projects]
    
    def get_summary(self) -> str:
        """Get a human-readable summary of the detection results."""
        if not self.is_successful():
            return f"Detection failed: {self.error_message}"
        
        if not self.has_projects():
            return "No projects detected"
        
        project_type = "monorepo" if self.is_monorepo else "single repository"
        config_info = f" (using {self.config_file_used})" if self.config_file_used else ""
        
        return f"Detected {self.get_project_count()} project(s) in {project_type}{config_info}"
