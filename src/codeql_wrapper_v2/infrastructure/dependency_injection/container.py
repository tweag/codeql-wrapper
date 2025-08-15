"""Dependency injection container implementation."""

import inspect
import logging
from typing import Any, Dict, Type, TypeVar, Optional, Callable, get_type_hints

from ...domain.interfaces.container_interface import DIContainer
from ...domain.exceptions.validation_exceptions import ValidationError

T = TypeVar('T')


class DIContainerImpl(DIContainer):
    """Dependency injection container implementation."""
    
    def __init__(self) -> None:
        """Initialize the container."""
        self._singletons: Dict[Type, Any] = {}
        self._singleton_factories: Dict[Type, Type] = {}
        self._transient_factories: Dict[Type, Type] = {}
        self._instances: Dict[Type, Any] = {}
        self._logger = logging.getLogger(__name__)
    
    def register_singleton(self, interface: Type[T], implementation: Type[T]) -> None:
        """Register a singleton service."""
        self._singleton_factories[interface] = implementation
        self._logger.debug(f"Registered singleton: {interface.__name__} -> {implementation.__name__}")
    
    def register_transient(self, interface: Type[T], implementation: Type[T]) -> None:
        """Register a transient service (new instance each time)."""
        self._transient_factories[interface] = implementation
        self._logger.debug(f"Registered transient: {interface.__name__} -> {implementation.__name__}")
    
    def register_instance(self, interface: Type[T], instance: T) -> None:
        """Register a specific instance."""
        self._instances[interface] = instance
        self._logger.debug(f"Registered instance: {interface.__name__}")
    
    def get(self, service_type: Type[T]) -> T:
        """Resolve a service of the given type."""
        service = self.get_optional(service_type)
        if service is None:
            raise ValidationError(f"Service of type {service_type.__name__} not registered")
        return service
    
    def get_optional(self, service_type: Type[T]) -> Optional[T]:
        """Resolve a service of the given type, returning None if not found."""
        # Check instances first
        if service_type in self._instances:
            return self._instances[service_type]
        
        # Check singletons
        if service_type in self._singletons:
            return self._singletons[service_type]
        
        # Create singleton if registered
        if service_type in self._singleton_factories:
            instance = self._create_instance(self._singleton_factories[service_type])
            self._singletons[service_type] = instance
            return instance
        
        # Create transient instance if registered
        if service_type in self._transient_factories:
            return self._create_instance(self._transient_factories[service_type])
        
        return None
    
    def _create_instance(self, implementation_type: Type[T]) -> T:
        """Create an instance of the given type, resolving dependencies."""
        try:
            # Get constructor signature
            signature = inspect.signature(implementation_type.__init__)
            
            # Prepare arguments for constructor
            kwargs = {}
            
            # Get type hints for the constructor
            type_hints = get_type_hints(implementation_type.__init__)
            
            for param_name, param in signature.parameters.items():
                if param_name == 'self':
                    continue
                
                # Get the parameter type from type hints
                param_type = type_hints.get(param_name)
                
                if param_type is not None:
                    # Try to resolve the dependency
                    dependency = self.get_optional(param_type)
                    if dependency is not None:
                        kwargs[param_name] = dependency
                    elif param.default == inspect.Parameter.empty:
                        # Required parameter but couldn't resolve
                        self._logger.warning(
                            f"Could not resolve required dependency {param_name}: {param_type} "
                            f"for {implementation_type.__name__}"
                        )
            
            # Create the instance
            instance = implementation_type(**kwargs)
            self._logger.debug(f"Created instance of {implementation_type.__name__}")
            return instance
            
        except Exception as e:
            self._logger.error(f"Failed to create instance of {implementation_type.__name__}: {e}")
            raise ValidationError(f"Failed to create instance of {implementation_type.__name__}: {e}")
