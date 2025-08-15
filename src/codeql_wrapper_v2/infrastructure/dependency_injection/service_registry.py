"""Service registration and configuration for dependency injection."""

import logging
from pathlib import Path
from typing import Optional

from .container import DIContainerImpl
from codeql_wrapper_v2.domain.interfaces.codeql_service import CodeQLService
from codeql_wrapper_v2.domain.interfaces.configuration_reader import FileSystemAnalyzer, ConfigurationReader
from codeql_wrapper_v2.domain.interfaces.analysis_service import AnalysisService
from codeql_wrapper_v2.domain.interfaces.project_detector import ProjectDetector as ProjectDetectorInterface, LanguageDetector
from codeql_wrapper_v2.application.use_cases.install_codeql_use_case import InstallCodeQLUseCase
from codeql_wrapper_v2.application.use_cases.detect_projects_use_case import DetectProjectsUseCase
from codeql_wrapper_v2.application.use_cases.run_codeql_analysis_use_case import AnalyzeRepositoryUseCase
from codeql_wrapper_v2.infrastructure.services.codeql_service import CodeQLServiceImpl
from codeql_wrapper_v2.infrastructure.file_system.file_system_analyzer import FileSystemAnalyzerImpl
from codeql_wrapper_v2.infrastructure.file_system.configuration_reader import JsonConfigurationReader
from codeql_wrapper_v2.infrastructure.services.language_detector import LanguageDetectorImpl
from codeql_wrapper_v2.infrastructure.services.project_detector import ProjectDetectorImpl
from codeql_wrapper_v2.infrastructure.services.repository_analysis_service import ProjectAnalysisServiceImpl


class ServiceRegistry:
    """Registry for configuring and managing service dependencies."""
    
    def __init__(self) -> None:
        """Initialize the service registry."""
        self._container = DIContainerImpl()
        self._is_configured = False
    
    def configure(
        self,
        installation_directory: Optional[str] = None,
        github_token: Optional[str] = None
    ) -> None:
        """Configure all services and their dependencies."""
        if self._is_configured:
            return
        
        logger = logging.getLogger(__name__)
        
        # Register logger instance - this will be used for Optional[logging.Logger] parameters
        self._container.register_instance(logging.Logger, logger)
        
        # Register CodeQL service with configuration
        from codeql_wrapper_v2.infrastructure.services.codeql_service import create_codeql_service
        
        # Create CodeQL service instance with configuration using the factory
        codeql_service = create_codeql_service(
            installation_directory=installation_directory,
            github_token=github_token
        )
        self._container.register_instance(CodeQLService, codeql_service)
        
        # Register file system services
        self._container.register_transient(FileSystemAnalyzer, FileSystemAnalyzerImpl)
        self._container.register_transient(ConfigurationReader, JsonConfigurationReader)
        self._container.register_transient(LanguageDetector, LanguageDetectorImpl)
        self._container.register_transient(ProjectDetectorInterface, ProjectDetectorImpl)
        self._container.register_transient(AnalysisService, ProjectAnalysisServiceImpl)
        
        # Register use cases (transient - new instance for each request)
        self._container.register_transient(InstallCodeQLUseCase, InstallCodeQLUseCase)
        self._container.register_transient(DetectProjectsUseCase, DetectProjectsUseCase)
        self._container.register_transient(AnalyzeRepositoryUseCase, AnalyzeRepositoryUseCase)
        
        self._is_configured = True
        logger.debug("Service registry configured successfully")
    
    def get_container(self) -> DIContainerImpl:
        """Get the configured DI container."""
        if not self._is_configured:
            self.configure()
        return self._container
    
    def reset(self) -> None:
        """Reset the registry (mainly for testing)."""
        self._container = DIContainerImpl()
        self._is_configured = False


# Global service registry instance
_service_registry: Optional[ServiceRegistry] = None


def get_service_registry() -> ServiceRegistry:
    """Get the global service registry instance."""
    global _service_registry
    if _service_registry is None:
        _service_registry = ServiceRegistry()
    return _service_registry
