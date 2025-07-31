"""Infrastructure-level exceptions for OS operations."""


class OSOperationError(Exception):
    """Base exception for OS operation failures."""
    
    def __init__(self, message: str, operation: str = "", path: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.operation = operation
        self.path = path
    
    def __str__(self) -> str:
        parts = [self.message]
        if self.operation:
            parts.append(f"Operation: {self.operation}")
        if self.path:
            parts.append(f"Path: {self.path}")
        return " | ".join(parts)


class FileSystemError(OSOperationError):
    """Exception raised when file system operations fail."""
    pass


class PermissionError(OSOperationError):
    """Exception raised when permission operations fail."""
    pass


class EnvironmentError(OSOperationError):
    """Exception raised when environment operations fail."""
    pass
