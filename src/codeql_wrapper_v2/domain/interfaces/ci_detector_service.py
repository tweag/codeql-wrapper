"""Service interface for comprehensive CI platform detection across multiple platforms."""

from abc import ABC, abstractmethod
from typing import List, Optional

from .ci_detector import CIDetector, CIEnvironmentInfo
from ..enumerators.platform import Platform


class CIDetectorService(ABC):
    """
    Service interface for detecting CI platform from multiple possible detectors.
    
    This service orchestrates multiple platform-specific detectors to identify
    the current CI environment and extract relevant information.
    """
    
    @abstractmethod
    def register_detector(self, detector: CIDetector) -> None:
        """
        Register a platform-specific CI detector.
        
        Args:
            detector: CI detector implementation for a specific platform
        """
        pass
    
    @abstractmethod
    def detect_current_platform(self) -> Optional[Platform]:
        """
        Detect the current CI platform from environment variables.
        
        Returns:
            Platform enum if detected, None if running locally or unknown platform
        """
        pass
    
    @abstractmethod
    def get_environment_info(self) -> CIEnvironmentInfo:
        """
        Get comprehensive environment information from the detected CI platform.
        
        Returns:
            Complete CI environment information
            
        Raises:
            CIDetectionError: If no CI platform is detected or environment is invalid
        """
        pass
    
    @abstractmethod
    def is_ci_environment(self) -> bool:
        """
        Check if code is currently running in any CI environment.
        
        Returns:
            True if running in a detected CI platform
        """
        pass
    
    @abstractmethod
    def get_supported_platforms(self) -> List[Platform]:
        """
        Get list of all supported CI platforms.
        
        Returns:
            List of platforms that have registered detectors
        """
        pass
    
    @abstractmethod
    def validate_ci_environment(self) -> tuple[bool, List[str]]:
        """
        Validate that the current CI environment is properly configured.
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        pass
    
    @abstractmethod
    def get_git_repository_context(self) -> tuple[str, str, Optional[str]]:
        """
        Extract Git repository context from CI environment.
        
        Returns:
            Tuple of (repository_name, ref, base_ref)
            
        Raises:
            CIDetectionError: If Git context cannot be determined
        """
        pass