"""Analysis-specific domain exceptions."""

from typing import Optional

class AnalysisError(Exception):
    """Base exception for CodeQL analysis errors."""
    
    def __init__(self, message: str, analysis_id: Optional[str] = None, project_path: Optional[str] = None) -> None:
        super().__init__(message)
        self.analysis_id = analysis_id
        self.project_path = project_path
        self.message = message
    
    def __str__(self) -> str:
        parts = [self.message]
        if self.analysis_id:
            parts.append(f"Analysis ID: {self.analysis_id}")
        if self.project_path:
            parts.append(f"Project: {self.project_path}")
        return " | ".join(parts)


class AnalysisValidationError(AnalysisError):
    """Exception raised when analysis configuration is invalid."""
    pass


class AnalysisTimeoutError(AnalysisError):
    """Exception raised when analysis exceeds timeout limits."""
    
    def __init__(self, message: str, timeout_minutes: int, **kwargs) -> None:
        super().__init__(message, **kwargs)
        self.timeout_minutes = timeout_minutes


class AnalysisConfigurationError(AnalysisError):
    """Exception raised when CodeQL configuration is invalid."""
    
    def __init__(self, message: str, configuration_issue: str, **kwargs) -> None:
        super().__init__(message, **kwargs)
        self.configuration_issue = configuration_issue


class DatabaseCreationError(AnalysisError):
    """Exception raised when CodeQL database creation fails."""
    
    def __init__(self, message: str, language: str, **kwargs) -> None:
        super().__init__(message, **kwargs)
        self.language = language


class QueryExecutionError(AnalysisError):
    """Exception raised when CodeQL query execution fails."""
    
    def __init__(self, message: str, query_pack: str, **kwargs) -> None:
        super().__init__(message, **kwargs)
        self.query_pack = query_pack