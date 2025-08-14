"""Data Transfer Objects for CLI output formatting."""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum


class OutputStatus(Enum):
    """Status codes for CLI operations."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class CLIOutput:
    """Base CLI output structure."""
    
    status: OutputStatus
    message: str
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON output."""
        result: Dict[str, Any] = {
            "status": self.status.value,
            "message": self.message
        }
        if self.details:
            result["details"] = self.details
        return result


@dataclass(frozen=True)
class InstallationOutput(CLIOutput):
    """Output for CodeQL installation operations."""
    
    version: Optional[str] = None
    installation_path: Optional[str] = None
    is_latest: Optional[bool] = None
    available_latest: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with installation-specific details."""
        result = super().to_dict()
        
        installation_details = {}
        if self.version:
            installation_details["version"] = self.version
        if self.installation_path:
            installation_details["installation_path"] = self.installation_path
        if self.is_latest is not None:
            installation_details["is_latest"] = self.is_latest
        if self.available_latest:
            installation_details["available_latest"] = self.available_latest
            
        if installation_details:
            result["installation"] = installation_details
            
        return result


@dataclass(frozen=True)
class DetectionOutput(CLIOutput):
    """Output for project detection operations."""
    
    repository_name: Optional[str] = None
    repository_path: Optional[str] = None
    is_monorepo: Optional[bool] = None
    project_count: Optional[int] = None
    config_file_used: Optional[str] = None
    projects: Optional[list] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with detection-specific details."""
        result = super().to_dict()
        
        detection_details = {}
        if self.repository_name:
            detection_details["repository_name"] = self.repository_name
        if self.repository_path:
            detection_details["repository_path"] = self.repository_path
        if self.is_monorepo is not None:
            detection_details["is_monorepo"] = self.is_monorepo
        if self.project_count is not None:
            detection_details["project_count"] = self.project_count
        if self.config_file_used:
            detection_details["config_file_used"] = self.config_file_used
        if self.projects:
            detection_details["projects"] = self.projects
            
        if detection_details:
            result["detection"] = detection_details
            
        return result
    
@dataclass(frozen=True)
class AnalyzeOutput(CLIOutput):
    """Output for project analysis operations."""

    repository_name: Optional[str] = None
    repository_path: Optional[str] = None
    is_monorepo: Optional[bool] = None
    project_count: Optional[int] = None
    config_file_used: Optional[str] = None
    successful_projects: Optional[list] = None
    failed_projects: Optional[list] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with analysis-specific details."""
        result = super().to_dict()

        analysis_details = {}
        if self.repository_name:
            analysis_details["repository_name"] = self.repository_name
        if self.repository_path:
            analysis_details["repository_path"] = self.repository_path
        if self.is_monorepo is not None:
            analysis_details["is_monorepo"] = self.is_monorepo
        if self.project_count is not None:
            analysis_details["project_count"] = self.project_count
        if self.config_file_used:
            analysis_details["config_file_used"] = self.config_file_used
        if self.successful_projects:
            analysis_details["successful_projects"] = self.successful_projects
        if self.failed_projects:
            analysis_details["failed_projects"] = self.failed_projects

        if analysis_details:
            result["analysis"] = analysis_details

        return result
