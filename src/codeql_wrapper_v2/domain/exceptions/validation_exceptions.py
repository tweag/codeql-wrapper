"""Validation-specific domain exceptions."""
from typing import Optional

class ValidationError(Exception):
    """Base exception for validation errors."""
    
    def __init__(self, message: str, field_name: Optional[str] = None, provided_value: Optional[str] = None) -> None:
        super().__init__(message)
        self.message = message
        self.field_name = field_name
        self.provided_value = provided_value
    
    def __str__(self) -> str:
        parts = [self.message]
        if self.field_name:
            parts.append(f"Field: {self.field_name}")
        if self.provided_value:
            parts.append(f"Value: {self.provided_value}")
        return " | ".join(parts)


class ProjectValidationError(ValidationError):
    """Exception raised when project structure validation fails."""
    pass


class LanguageValidationError(ValidationError):
    """Exception raised when language validation fails."""
    pass


class PathValidationError(ValidationError):
    """Exception raised when file path validation fails."""
    pass