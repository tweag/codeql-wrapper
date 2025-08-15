"""Dependency injection module exports."""

from ...domain.interfaces.container_interface import DIContainer
from .container import DIContainerImpl
from .service_registry import (
    ServiceRegistry,
    get_service_registry,
)

__all__ = [
    "DIContainer",
    "DIContainerImpl",
    "ServiceRegistry",
    "get_service_registry",
]
