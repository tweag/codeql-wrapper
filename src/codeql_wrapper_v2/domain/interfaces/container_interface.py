"""Dependency injection container interface."""

from abc import ABC, abstractmethod
from typing import TypeVar, Type, Optional

T = TypeVar('T')


class DIContainer(ABC):
    """Abstract base class for dependency injection containers."""
    
    @abstractmethod
    def register_singleton(self, interface: Type[T], implementation: Type[T]) -> None:
        """Register a singleton service."""
        pass
    
    @abstractmethod
    def register_transient(self, interface: Type[T], implementation: Type[T]) -> None:
        """Register a transient service (new instance each time)."""
        pass
    
    @abstractmethod
    def register_instance(self, interface: Type[T], instance: T) -> None:
        """Register a specific instance."""
        pass
    
    @abstractmethod
    def get(self, service_type: Type[T]) -> T:
        """Resolve a service of the given type."""
        pass
    
    @abstractmethod
    def get_optional(self, service_type: Type[T]) -> Optional[T]:
        """Resolve a service of the given type, returning None if not found."""
        pass
