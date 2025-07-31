"""CI/CD platform detection and integration exceptions."""


from typing import Optional


class CIDetectionError(Exception):
    """Base exception for CI platform detection errors."""

    def __init__(self, message: str, platform: Optional[str] = None, missing_variables: list[str] = []) -> None:
        super().__init__(message)
        self.message = message
        self.platform = platform
        self.missing_variables = missing_variables or []
    
    def __str__(self) -> str:
        parts = [self.message]
        if self.platform:
            parts.append(f"Platform: {self.platform}")
        if self.missing_variables:
            parts.append(f"Missing variables: {', '.join(self.missing_variables)}")
        return " | ".join(parts)


class UnsupportedCIPlatformError(CIDetectionError):
    """Exception raised when CI platform is not supported."""
    pass


class InvalidCIEnvironmentError(CIDetectionError):
    """Exception raised when CI environment is invalid or incomplete."""
    pass


class MissingEnvironmentVariablesError(CIDetectionError):
    """Exception raised when required environment variables are missing."""
    pass