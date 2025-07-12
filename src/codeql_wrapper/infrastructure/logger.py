"""Logging infrastructure for the CodeQL wrapper application."""

import logging
import sys
from typing import Optional
from contextvars import ContextVar

# Context variable to store the current project path
current_project_context: ContextVar[Optional[str]] = ContextVar(
    "current_project", default=None
)


class ShortNameFormatter(logging.Formatter):
    """Custom formatter that shows only the class name instead of full module path."""

    def format(self, record: logging.LogRecord) -> str:
        # Extract just the class name from the full module path
        if "." in record.name:
            record.name = record.name.split(".")[-1]

        # Add project field - use context if not explicitly set
        if not hasattr(record, "project"):
            record.project = current_project_context.get() or ""

        return super().format(record)


def get_logger(
    name: str, level: Optional[int] = None, format_string: Optional[str] = None
) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (usually __name__)
        level: Logging level (if None, inherits from root logger)
        format_string: Custom format string

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Avoid adding multiple handlers if logger already configured
    if logger.handlers:
        return logger

    # Set level - if not specified, inherit from root logger
    if level is not None:
        logger.setLevel(level)
    else:
        # Let the logger inherit from root logger (which is configured by configure_logging)
        logger.setLevel(logging.NOTSET)

    # Propagate to parent loggers (root logger) to use basicConfig
    # since we're using basicConfig for root logging
    logger.propagate = True  # Let root logger handle it

    # Only add handler if we want a custom format different from root
    if format_string is not None:
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler_level = level if level is not None else logger.getEffectiveLevel()
        handler.setLevel(handler_level)

        # Create formatter with our custom short name formatter
        formatter = ShortNameFormatter(format_string)
        handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(handler)

        # Disable propagation since we have our own handler
        logger.propagate = False

    return logger


def set_project_context(project_path: Optional[str]) -> None:
    """
    Set the current project context for logging.

    Args:
        project_path: The project path to set in context
    """
    current_project_context.set(str(project_path) if project_path else "")


def clear_project_context() -> None:
    """Clear the current project context."""
    current_project_context.set("")


def configure_logging(verbose: bool = False) -> None:
    """
    Configure global logging settings.

    Args:
        verbose: Enable verbose (DEBUG) logging
    """
    level = logging.DEBUG if verbose else logging.INFO

    # Clear any existing handlers to avoid duplicates
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    # Create a console handler with our custom formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    # Use our custom formatter that shows only class names
    formatter = ShortNameFormatter(
        "%(asctime)s - %(name)s - %(project)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    # Configure root logger
    root_logger.setLevel(level)
    root_logger.addHandler(handler)


def log_with_project(
    logger: logging.Logger, level: int, msg: str, project_path: Optional[str] = None
) -> None:
    """
    Log a message with project information.

    Args:
        logger: The logger instance
        level: Logging level (e.g., logging.INFO)
        msg: The message to log
        project_path: Optional project path to include in the log
    """
    # Create a log record
    record = logger.makeRecord(logger.name, level, "", 0, msg, (), None)

    # Add project information
    record.project = str(project_path) if project_path else ""

    # Handle the record
    logger.handle(record)
