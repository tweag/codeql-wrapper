"""Logging infrastructure for the CodeQL wrapper application."""

import logging
import sys
from typing import Optional
from contextvars import ContextVar

# Context variable to store the current project path
current_project_context: ContextVar[Optional[str]] = ContextVar(
    "current_project", default=None
)

# Context variable to store the current log color
current_log_color: ContextVar[Optional[str]] = ContextVar(
    "current_log_color", default=None
)

# Context variable to store the current log format
current_format: ContextVar[Optional[str]] = ContextVar(
    "current_format", default="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class ShortNameFormatter(logging.Formatter):
    """Custom formatter that shows only the class name instead of full module path."""

    def format(self, record: logging.LogRecord) -> str:
        # Extract just the class name from the full module path
        if "." in record.name:
            record.name = record.name.split(".")[-1]

        # Add project field - use context if not explicitly set
        project_value = current_project_context.get() or ""
        if not hasattr(record, "project"):
            record.project = project_value

        # Get the log color from context if available
        log_color = getattr(record, "log_color", None) or current_log_color.get()

        # Get the current format from context and update the formatter
        # If no specific format is set, determine format based on project context
        current_fmt = current_format.get()
        if current_fmt is None:
            if project_value:
                current_fmt = (
                    "%(asctime)s - %(name)s - %(project)s - %(levelname)s - %(message)s"
                )
            else:
                current_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        if current_fmt and current_fmt != self._style._fmt:
            self._style._fmt = current_fmt

        # Format the message with the parent formatter
        formatted_message = super().format(record)

        # Apply color if available
        if log_color:
            reset_color = "\033[0m"
            return f"{log_color}{formatted_message}{reset_color}"

        return formatted_message


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

    # Always use our custom formatter to ensure colors work
    if format_string is None:
        format_string = current_format.get()

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
    current_format.set(
        "%(asctime)s - %(name)s - %(project)s - %(levelname)s - %(message)s"
    )


def clear_project_context() -> None:
    """Clear the current project context."""
    current_project_context.set("")
    current_format.set("%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def set_log_color(log_color: Optional[str]) -> None:
    """
    Set the current log color for logging.

    Args:
        log_color: The ANSI color code to set for logs
    """
    current_log_color.set(log_color)


def clear_log_color() -> None:
    """Clear the current log color."""
    current_log_color.set(None)


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
    formatter = ShortNameFormatter(current_format.get())

    handler.setFormatter(formatter)

    # Configure root logger
    root_logger.setLevel(level)
    root_logger.addHandler(handler)
