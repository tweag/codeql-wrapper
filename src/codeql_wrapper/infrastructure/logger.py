"""Logging infrastructure for the hello world application."""

import logging
import sys
from typing import Optional


def get_logger(
    name: str, level: int = logging.INFO, format_string: Optional[str] = None
) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (usually __name__)
        level: Logging level
        format_string: Custom format string

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Avoid adding multiple handlers if logger already configured
    if logger.handlers:
        return logger

    # Set level
    logger.setLevel(level)

    # Propagate to parent loggers (root logger) to use basicConfig
    # since we're using basicConfig for root logging
    logger.propagate = True  # Let root logger handle it

    # Only add handler if we want a custom format different from root
    if format_string is not None:
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)

        # Create formatter
        formatter = logging.Formatter(format_string)
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

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,  # Force reconfiguration
    )
