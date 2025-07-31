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
