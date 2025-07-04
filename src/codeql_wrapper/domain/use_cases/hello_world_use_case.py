"""Hello World use case implementation."""

# import logging
from datetime import datetime
from typing import Any

from ..entities import GreetingRequest, GreetingResponse


class HelloWorldUseCase:
    """Use case for greeting operations following clean architecture principles."""

    def __init__(self, logger: Any) -> None:
        """Initialize the use case with dependencies."""
        self._logger = logger

    def execute(self, name: str) -> GreetingResponse:
        """
        Execute the hello world use case.

        Args:
            name: The name to greet

        Returns:
            GreetingResponse with the greeting message

        Raises:
            ValueError: If the name is invalid
        """
        try:
            self._logger.debug(f"Processing greeting request for name: {name}")

            # Create and validate request
            request = GreetingRequest(name=name.strip())

            # Execute business logic
            message = self._create_greeting_message(request.name)
            timestamp = datetime.now().isoformat()

            # Create response
            response = GreetingResponse(message=message, timestamp=timestamp)

            self._logger.info(f"Generated greeting: {response.message}")

            return response

        except ValueError as e:
            self._logger.error(f"Invalid request: {e}")
            raise
        except Exception as e:
            self._logger.error(f"Unexpected error in HelloWorldUseCase: {e}")
            raise RuntimeError(f"Failed to process greeting: {e}") from e

    def _create_greeting_message(self, name: str) -> str:
        """
        Create a greeting message for the given name.

        Args:
            name: The name to greet

        Returns:
            The formatted greeting message
        """
        return f"Hello, {name}!"
