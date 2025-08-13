"""Domain interfaces for repository abstractions."""

from .project_detector import ProjectDetector, LanguageDetector
from .configuration_reader import ConfigurationReader, FileSystemAnalyzer
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
    "CodeQLService",
    "CodeQLInstallationInfo",
    "CodeQLExecutionResult",
]