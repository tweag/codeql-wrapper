"""Domain exceptions for CodeQL wrapper application."""

from .analysis_exceptions import (
    AnalysisError,
    AnalysisValidationError,
    AnalysisTimeoutError,
    AnalysisConfigurationError,
    DatabaseCreationError,
    QueryExecutionError
)
from .validation_exceptions import (
    ValidationError,
    ProjectValidationError,
    LanguageValidationError,
    PathValidationError
)
from .ci_exceptions import (
    CIDetectionError,
    UnsupportedCIPlatformError,
    InvalidCIEnvironmentError,
    MissingEnvironmentVariablesError
)
from .codeql_exceptions import (
    CodeQLError,
    CodeQLNotInstalledError,
    CodeQLInstallationError,
    CodeQLVersionError,
    DatabaseCreationError,
    QueryExecutionError,
    DatabaseNotFoundError,
    CodeQLExecutionError
)

__all__ = [
    # Analysis exceptions
    "AnalysisError",
    "AnalysisValidationError", 
    "AnalysisTimeoutError",
    "AnalysisConfigurationError",
    "DatabaseCreationError",
    "QueryExecutionError",
    
    # Validation exceptions
    "ValidationError",
    "ProjectValidationError",
    "LanguageValidationError",
    "PathValidationError",
    
    # CI exceptions
    "CIDetectionError",
    "UnsupportedCIPlatformError",
    "InvalidCIEnvironmentError",
    "MissingEnvironmentVariablesError",
    
    # CodeQL exceptions
    "CodeQLError",
    "CodeQLNotInstalledError",
    "CodeQLInstallationError",
    "CodeQLVersionError", 
    "DatabaseNotFoundError",
    "CodeQLExecutionError",
]