"""Interface for detecting CI/CD platform and extracting environment information."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass

from ..enumerators.platform import Platform


@dataclass(frozen=True)
class CIEnvironmentInfo:
    """Value object containing CI environment information."""
    
    platform: Platform
    is_ci_environment: bool
    environment_variables: Dict[str, str]
    
    # Common CI information
    repository_name: Optional[str] = None
    branch_name: Optional[str] = None
    commit_sha: Optional[str] = None
    build_number: Optional[str] = None
    build_url: Optional[str] = None
    
    # Pull request specific information
    is_pull_request: bool = False
    pull_request_number: Optional[str] = None
    base_branch: Optional[str] = None
    base_commit_sha: Optional[str] = None
    
    # Actor information
    triggered_by: Optional[str] = None
    actor_email: Optional[str] = None
    
    def has_git_reference_info(self) -> bool:
        """Check if environment contains necessary Git reference information."""
        return bool(self.commit_sha and (self.branch_name or self.is_pull_request))
    
    def get_display_name(self) -> str:
        """Get human-readable platform name."""
        return self.platform.get_display_name()
    
    def supports_sarif_upload(self) -> bool:
        """Check if CI platform supports SARIF result upload."""
        return self.platform.supports_sarif_upload()


class CIDetector(ABC):
    """
    Abstract interface for detecting CI/CD platform and extracting environment information.
    
    Each CI platform (GitHub Actions, GitLab CI, Azure DevOps, etc.) should implement
    this interface to provide platform-specific detection and data extraction logic.
    """
    
    @abstractmethod
    def can_detect(self) -> bool:
        """
        Check if this detector can identify its CI platform from environment variables.
        
        Returns:
            True if the current environment appears to be this CI platform
        """
        pass
    
    @abstractmethod
    def get_platform_type(self) -> Platform:
        """
        Get the platform type this detector handles.
        
        Returns:
            Platform enumeration value for this CI system
        """
        pass
    
    @abstractmethod
    def extract_environment_info(self) -> CIEnvironmentInfo:
        """
        Extract all relevant CI environment information from environment variables.
        
        Returns:
            Complete CI environment information including Git refs and build context
            
        Raises:
            CIDetectionError: If environment cannot be properly parsed
        """
        pass
    
    @abstractmethod
    def validate_environment(self) -> tuple[bool, list[str]]:
        """
        Validate that the CI environment has all necessary information for analysis.
        
        Returns:
            Tuple of (is_valid, list_of_missing_variables)
        """
        pass
    
    def get_git_reference_info(self) -> tuple[str, Optional[str]]:
        """
        Extract Git reference information (ref, base_ref) from CI environment.
        
        Returns:
            Tuple of (ref, base_ref) where base_ref is None for non-PR builds
        """
        env_info = self.extract_environment_info()
        
        if env_info.is_pull_request:
            # For PRs, construct the PR ref and use base branch as base_ref
            pr_ref = f"refs/pull/{env_info.pull_request_number}/merge"
            base_ref = f"refs/heads/{env_info.base_branch}" if env_info.base_branch else None
            return pr_ref, base_ref
        elif env_info.branch_name:
            # For branch builds
            branch_ref = f"refs/heads/{env_info.branch_name}"
            return branch_ref, None
        else:
            # Fallback to commit-only reference
            return f"refs/commit/{env_info.commit_sha}", None
