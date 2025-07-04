"""Greeting domain entities for the hello world application."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class GreetingRequest:
    """Request entity for greeting operations."""

    name: str

    def __post_init__(self) -> None:
        """Validate the greeting request."""
        if not self.name or not self.name.strip():
            raise ValueError("Name cannot be empty or whitespace")


@dataclass(frozen=True)
class GreetingResponse:
    """Response entity for greeting operations."""

    message: str
    timestamp: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate the greeting response."""
        if not self.message:
            raise ValueError("Message cannot be empty")
