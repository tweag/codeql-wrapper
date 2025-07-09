"""Logging infrastructure for the hello world application."""

import logging
import sys
from typing import Optional


class ShortNameFormatter(logging.Formatter):
    """Custom formatter that shows only the class name instead of full module path."""

    def format(self, record: logging.LogRecord) -> str:
        # Extract just the class name from the full module path
        if "." in record.name:
            record.name = record.name.split(".")[-1]
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
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    # Configure root logger
    root_logger.setLevel(level)
    root_logger.addHandler(handler)
