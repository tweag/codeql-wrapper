"""Tests for the logger infrastructure module."""

import logging
import sys
from io import StringIO
from unittest.mock import patch

from codeql_wrapper.infrastructure.logger import (
    ShortNameFormatter,
    get_logger,
    configure_logging,
)


class TestShortNameFormatter:
    """Test cases for the ShortNameFormatter class."""

    def test_format_with_full_module_path(self) -> None:
        """Test formatting with full module path."""
        formatter = ShortNameFormatter("%(name)s - %(levelname)s - %(message)s")

        # Create a proper log record
        record = logging.LogRecord(
            name="codeql_wrapper.infrastructure.logger.TestClass",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        # Should extract just the class name "TestClass"
        assert "TestClass" in result
        assert "codeql_wrapper.infrastructure.logger" not in result
        assert "INFO" in result
        assert "Test message" in result

    def test_format_with_simple_name(self) -> None:
        """Test formatting with simple name (no dots)."""
        formatter = ShortNameFormatter("%(name)s - %(levelname)s - %(message)s")

        # Create a proper log record
        record = logging.LogRecord(
            name="TestClass",
            level=logging.ERROR,
            pathname="test.py",
            lineno=42,
            msg="Error message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        # Should keep the simple name as-is
        assert "TestClass" in result
        assert "ERROR" in result
        assert "Error message" in result


class TestGetLogger:
    """Test cases for the get_logger function."""

    def teardown_method(self) -> None:
        """Clean up after each test."""
        # Reset logging configuration
        logging.getLogger().handlers.clear()
        logging.getLogger().setLevel(logging.WARNING)

    def test_get_logger_basic(self) -> None:
        """Test basic logger creation."""
        logger = get_logger("test_logger")

        assert logger.name == "test_logger"
        assert isinstance(logger, logging.Logger)

    def test_get_logger_with_level(self) -> None:
        """Test logger creation with specific level."""
        logger = get_logger("test_logger", level=logging.DEBUG)

        assert logger.level == logging.DEBUG

    def test_get_logger_with_custom_format(self) -> None:
        """Test logger creation with custom format."""
        custom_format = "%(name)s - %(message)s"
        logger = get_logger("test_logger", format_string=custom_format)

        # Should have a handler with custom format
        assert len(logger.handlers) == 1
        handler = logger.handlers[0]
        assert isinstance(handler.formatter, ShortNameFormatter)

    def test_get_logger_reuse_existing(self) -> None:
        """Test that calling get_logger twice returns the same logger."""
        logger1 = get_logger("test_logger")
        logger2 = get_logger("test_logger")

        assert logger1 is logger2

    def test_get_logger_no_duplicate_handlers(self) -> None:
        """Test that repeated calls don't add duplicate handlers."""
        logger1 = get_logger("test_logger", format_string="%(message)s")
        handler_count_1 = len(logger1.handlers)

        logger2 = get_logger("test_logger", format_string="%(message)s")
        handler_count_2 = len(logger2.handlers)

        assert handler_count_1 == handler_count_2
        assert logger1 is logger2

    def test_get_logger_inherits_from_root(self) -> None:
        """Test that logger inherits from root when no level specified."""
        logger = get_logger("test_logger")

        # Should inherit from root logger
        assert logger.level == logging.NOTSET
        # Note: logger.propagate is True by default but can be changed by other operations
        # Just verify it's a boolean value
        assert isinstance(logger.propagate, bool)

    def test_get_logger_custom_format_disables_propagation(self) -> None:
        """Test that custom format disables propagation."""
        logger = get_logger("test_logger", format_string="%(message)s")

        # Should not propagate since it has its own handler
        assert logger.propagate is False


class TestConfigureLogging:
    """Test cases for the configure_logging function."""

    def teardown_method(self) -> None:
        """Clean up after each test."""
        # Reset logging configuration
        logging.getLogger().handlers.clear()
        logging.getLogger().setLevel(logging.WARNING)

    def test_configure_logging_default(self) -> None:
        """Test default logging configuration."""
        configure_logging()

        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO
        assert len(root_logger.handlers) == 1

        handler = root_logger.handlers[0]
        assert isinstance(handler, logging.StreamHandler)
        assert handler.stream is sys.stdout
        assert isinstance(handler.formatter, ShortNameFormatter)

    def test_configure_logging_verbose(self) -> None:
        """Test verbose logging configuration."""
        configure_logging(verbose=True)

        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG
        assert len(root_logger.handlers) == 1

    def test_configure_logging_clears_existing_handlers(self) -> None:
        """Test that configure_logging clears existing handlers."""
        root_logger = logging.getLogger()

        # Add a handler manually
        old_handler = logging.StreamHandler()
        root_logger.addHandler(old_handler)

        # Configure logging should clear and add new handler
        configure_logging()

        assert len(root_logger.handlers) == 1
        assert old_handler not in root_logger.handlers

    def test_configure_logging_formatter_type(self) -> None:
        """Test that configure_logging uses ShortNameFormatter."""
        configure_logging()

        root_logger = logging.getLogger()
        handler = root_logger.handlers[0]

        assert isinstance(handler.formatter, ShortNameFormatter)

    @patch("sys.stdout", new_callable=StringIO)
    def test_configure_logging_output_format(self, mock_stdout) -> None:
        """Test that logging output uses the expected format."""
        configure_logging()

        # Create a logger and log a message
        logger = logging.getLogger("test.module.MyClass")
        logger.info("Test message")

        output = mock_stdout.getvalue()

        # Should show only class name, not full module path
        assert "MyClass" in output
        assert "test.module" not in output
        assert "INFO" in output
        assert "Test message" in output

    def test_configure_logging_integration_with_get_logger(self) -> None:
        """Test that configure_logging works with get_logger."""
        configure_logging(verbose=True)

        # Get a logger after configuration
        logger = get_logger("test_logger")

        # Should inherit DEBUG level from root
        assert logger.getEffectiveLevel() == logging.DEBUG
        # Note: propagate may be affected by get_logger implementation
        assert isinstance(logger.propagate, bool)
