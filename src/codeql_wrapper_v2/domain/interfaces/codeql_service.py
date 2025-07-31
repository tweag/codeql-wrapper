"""Interface for CodeQL CLI operations and management."""

from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class CodeQLInstallationInfo:
    """Value object containing CodeQL installation information."""
    
    is_installed: bool
    version: Optional[str] = None
    installation_path: Optional[str] = None
    is_latest_version: bool = False
    available_latest_version: Optional[str] = None
    
    def needs_upgrade(self) -> bool:
        """Check if CodeQL installation needs to be upgraded."""
        return (
            self.is_installed and 
            not self.is_latest_version and 
            self.available_latest_version is not None
        )
    
    def get_version_info(self) -> str:
        """Get formatted version information."""
        if not self.is_installed:
            return "CodeQL not installed"
        
        version_info = f"CodeQL {self.version}"
        if self.needs_upgrade():
            version_info += f" (latest: {self.available_latest_version})"
        elif self.is_latest_version:
            version_info += " (latest)"
        
        return version_info

@dataclass(frozen=True)
class CodeQLExecutionResult:
    """Result of CodeQL command execution."""
    
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    execution_time_seconds: float
    command_executed: str
    
    def has_errors(self) -> bool:
        """Check if execution had errors."""
        return not self.success or self.exit_code != 0
    
    def get_error_summary(self) -> str:
        """Get formatted error summary."""
        if not self.has_errors():
            return "No errors"
        
        error_parts = []
        if self.exit_code != 0:
            error_parts.append(f"Exit code: {self.exit_code}")
        
        if self.stderr.strip():
            error_parts.append(f"Error: {self.stderr.strip()}")
        
        return " | ".join(error_parts)

class CodeQLService(ABC):
    """
    Abstract interface for CodeQL CLI operations and management.
    
    This interface provides a clean abstraction for all CodeQL-related operations,
    allowing different implementations (local CLI, containerized, cloud-based) while
    keeping the domain logic independent of infrastructure concerns.
    """
    
    @abstractmethod
    async def validate_installation(self) -> CodeQLInstallationInfo:
        """
        Validate CodeQL CLI installation and version.
        
        Returns:
            Installation information including version and upgrade availability
        """
        pass

    @abstractmethod
    async def get_latest_version(self) -> str:
        """
        Get the latest version of CodeQL CLI.
        
        Returns:
            CodeQL version string (e.g. "2.10.0")

        """
        pass
    
    @abstractmethod
    async def install(
        self, 
        version: str, 
        force_reinstall: bool = False, 
        persistent_path: bool = True
    ) -> CodeQLInstallationInfo:
        """
        Install or upgrade CodeQL CLI to a specific version.
        
        Args:
            version: The version of CodeQL CLI to install
            force_reinstall: Whether to reinstall even if latest version exists
            persistent_path: Whether to make PATH changes persistent across sessions
            
        Returns:
            Installation information after installation attempt
            
        Raises:
            CodeQLInstallationError: If installation fails
        """
        pass
    
    @abstractmethod
    async def execute_command(
        self,
        command_args: List[str],
        working_directory: Optional[str] = None,
        timeout_seconds: Optional[int] = None
    ) -> CodeQLExecutionResult:
        """
        Execute arbitrary CodeQL CLI command with arguments.
        
        Args:
            command_args: List of command arguments (excluding 'codeql')
            working_directory: Directory to execute command in
            timeout_seconds: Maximum execution time
            
        Returns:
            Raw execution result
            
        Raises:
            CodeQLExecutionError: If command execution fails
        """
        pass
    
 