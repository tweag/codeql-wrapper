"""Domain interfaces for repository abstractions."""

from .project_detector import ProjectDetector, LanguageDetector
from .configuration_reader import ConfigurationReader, FileSystemAnalyzer
from .ci_detector import CIDetector, CIEnvironmentInfo
from .ci_detector_service import CIDetectorService
from .codeql_service import (
    CodeQLService,
    CodeQLInstallationInfo,
    CodeQLExecutionResult
)

__all__ = [
    "ProjectDetector",
    "LanguageDetector",
    "ConfigurationReader",
    "FileSystemAnalyzer",
    "CIDetector",
    "CIEnvironmentInfo", 
    "CIDetectorService",
    "CodeQLService",
    "CodeQLInstallationInfo",
    "CodeQLExecutionResult",
]