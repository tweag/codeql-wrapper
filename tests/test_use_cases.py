"""Tests for the use cases module."""

# import logging
from unittest.mock import Mock

import pytest

from codeql_wrapper.domain.entities import GreetingRequest, GreetingResponse
from codeql_wrapper.domain.use_cases import HelloWorldUseCase


class TestGreetingRequest:
    """Test cases for GreetingRequest entity."""

    def test_valid_request(self) -> None:
        """Test creating a valid greeting request."""
        request = GreetingRequest(name="John")
        assert request.name == "John"

    def test_empty_name_raises_error(self) -> None:
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="Name cannot be empty or whitespace"):
            GreetingRequest(name="")

    def test_whitespace_name_raises_error(self) -> None:
        """Test that whitespace-only name raises ValueError."""
        with pytest.raises(ValueError, match="Name cannot be empty or whitespace"):
            GreetingRequest(name="   ")


class TestGreetingResponse:
    """Test cases for GreetingResponse entity."""

    def test_valid_response(self) -> None:
        """Test creating a valid greeting response."""
        response = GreetingResponse(message="Hello, World!")
        assert response.message == "Hello, World!"
        assert response.timestamp is None

    def test_response_with_timestamp(self) -> None:
        """Test creating a response with timestamp."""
        timestamp = "2025-07-04T10:00:00"
        response = GreetingResponse(message="Hello, World!", timestamp=timestamp)
        assert response.message == "Hello, World!"
        assert response.timestamp == timestamp

    def test_empty_message_raises_error(self) -> None:
        """Test that empty message raises ValueError."""
        with pytest.raises(ValueError, match="Message cannot be empty"):
            GreetingResponse(message="")


class TestHelloWorldUseCase:
    """Test cases for HelloWorldUseCase."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.mock_logger = Mock()
        self.use_case = HelloWorldUseCase(self.mock_logger)

    def test_execute_success(self) -> None:
        """Test successful execution of the use case."""
        # Act
        result = self.use_case.execute("John")

        # Assert
        assert isinstance(result, GreetingResponse)
        assert result.message == "Hello, John!"
        assert result.timestamp is not None

        # Verify logging
        self.mock_logger.debug.assert_called()
        self.mock_logger.info.assert_called_with("Generated greeting: Hello, John!")

    def test_execute_with_whitespace_name(self) -> None:
        """Test execution with whitespace around name."""
        # Act
        result = self.use_case.execute("  Jane  ")

        # Assert
        assert result.message == "Hello, Jane!"

        # Verify logging
        self.mock_logger.debug.assert_called_with(
            "Processing greeting request for name:   Jane  "
        )

    def test_execute_with_empty_name_raises_error(self) -> None:
        """Test that empty name raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError):
            self.use_case.execute("")

        # Verify error logging
        self.mock_logger.error.assert_called()

    def test_execute_with_whitespace_only_name_raises_error(self) -> None:
        """Test that whitespace-only name raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError):
            self.use_case.execute("   ")

        # Verify error logging
        self.mock_logger.error.assert_called()

    def test_create_greeting_message(self) -> None:
        """Test the private greeting message creation method."""
        # Access private method for testing
        message = self.use_case._create_greeting_message("Alice")
        assert message == "Hello, Alice!"
