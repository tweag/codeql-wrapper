"""Domain interfaces for repository abstractions."""

#from .project_detector import ProjectDetector
from .ci_detector import CIDetector, CIEnvironmentInfo
from .ci_detector_service import CIDetectorService
from .codeql_service import (
    CodeQLService,
    CodeQLInstallationInfo,
    CodeQLExecutionResult
)

__all__ = [
#    "ProjectDetector",
    "CIDetector",
    "CIEnvironmentInfo", 
    "CIDetectorService",
    "CodeQLService",
    "CodeQLInstallationInfo",
    "CodeQLExecutionResult",
]