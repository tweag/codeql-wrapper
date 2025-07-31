"""CodeQL-specific domain exceptions."""


from typing import Optional


class CodeQLError(Exception):
    """Base exception for CodeQL operations."""
    
    def __init__(self, message: str, command: Optional[str] = None, exit_code: int = 0) -> None:
        super().__init__(message)
        self.message = message
        self.command = command
        self.exit_code = exit_code
    
    def __str__(self) -> str:
        parts = [self.message]
        if self.command:
            parts.append(f"Command: {self.command}")
        if self.exit_code is not None:
            parts.append(f"Exit code: {self.exit_code}")
        return " | ".join(parts)


class CodeQLNotInstalledError(CodeQLError):
    """Exception raised when CodeQL CLI is not installed or not found."""
    pass


class CodeQLInstallationError(CodeQLError):
    """Exception raised when CodeQL installation fails."""
    
    def __init__(self, message: str, installation_path: str, **kwargs) -> None:
        super().__init__(message, **kwargs)
        self.installation_path = installation_path


class CodeQLVersionError(CodeQLError):
    """Exception raised when CodeQL version is incompatible."""

    def __init__(self, message: str, current_version: str, required_version: str, **kwargs) -> None:
        super().__init__(message, **kwargs)
        self.current_version = current_version
        self.required_version = required_version


class DatabaseCreationError(CodeQLError):
    """Exception raised when CodeQL database creation fails."""
    
    def __init__(self, message: str, project_path: str, language: str, **kwargs) -> None:
        super().__init__(message, **kwargs)
        self.project_path = project_path
        self.language = language


class QueryExecutionError(CodeQLError):
    """Exception raised when CodeQL query execution fails."""

    def __init__(self, message: str, query_pack: str, database_path: str, **kwargs) -> None:
        super().__init__(message, **kwargs)
        self.query_pack = query_pack
        self.database_path = database_path


class DatabaseNotFoundError(CodeQLError):
    """Exception raised when CodeQL database is not found or invalid."""
    
    def __init__(self, message: str, database_path: str, **kwargs) -> None:
        super().__init__(message, **kwargs)
        self.database_path = database_path


class CodeQLExecutionError(CodeQLError):
    """Exception raised when CodeQL command execution fails."""
    
    def __init__(self, message: str, stderr: str, **kwargs) -> None:
        super().__init__(message, **kwargs)
        self.stderr = stderr