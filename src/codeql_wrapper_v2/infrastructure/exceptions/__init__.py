"""Infrastructure exceptions module."""

from .os_exceptions import OSOperationError, FileSystemError, PermissionError, EnvironmentError

__all__ = [
    "OSOperationError",
    "FileSystemError", 
    "PermissionError",
    "EnvironmentError"
]
