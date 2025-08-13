"""Project detector implementation."""

import logging
from pathlib import Path
from typing import Optional

from codeql_wrapper_v2.domain.entities.detect_projects_request import DetectProjectsRequest
from codeql_wrapper_v2.domain.entities.detect_projects_result import DetectProjectsResult
from codeql_wrapper_v2.domain.entities.repository import Repository
from codeql_wrapper_v2.domain.interfaces.project_detector import ProjectDetector, LanguageDetector
from codeql_wrapper_v2.domain.interfaces.configuration_reader import ConfigurationReader, FileSystemAnalyzer
from codeql_wrapper_v2.domain.services.project_detection_service import ProjectDetectionDomainService


class ProjectDetectorImpl(ProjectDetector):
    """Implementation of project detection for repositories."""
    
    def __init__(
        self,
        language_detector: LanguageDetector,
        config_reader: ConfigurationReader,
        file_system_analyzer: FileSystemAnalyzer,
        logger: Optional[logging.Logger] = None
    ) -> None:
        """Initialize the project detector with its dependencies."""
        self._logger = logger or logging.getLogger(__name__)
        self._detection_service = ProjectDetectionDomainService(
            language_detector=language_detector,
            config_reader=config_reader,
            file_system_analyzer=file_system_analyzer,
            logger=self._logger
        )
    
    async def detect_projects(self, request: DetectProjectsRequest) -> DetectProjectsResult:
        """
        Detect all projects within a repository based on the request parameters.
        
        Args:
            request: Project detection request with all parameters
            
        Returns:
            DetectProjectsResult containing detected projects and metadata
        """
        self._logger.info(f"Starting project detection in: {request.repository_path}")
        
        try:
            result = await self._detection_service.detect_projects(request)
            
            self._logger.info(f"Project detection completed: {result.get_summary()}")
            return result
            
        except Exception as e:
            self._logger.error(f"Project detection failed: {e}")
            repository = Repository(path=request.repository_path)
            return DetectProjectsResult(
                repository=repository,
                detected_projects=[],
                is_monorepo=False,
                error_message=str(e)
            )
    
    async def is_monorepo(self, repository_path: Path) -> bool:
        """
        Determine if repository follows monorepo structure.
        
        Args:
            repository_path: Path to the repository root
            
        Returns:
            True if repository contains multiple projects
        """
        try:
            # Quick check - look for multiple subdirectories with project indicators
            project_dirs = []
            
            for item in repository_path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    # Check if directory has project indicators
                    if await self._has_project_indicators(item):
                        project_dirs.append(item)
            
            # Also check for .codeql.json configuration
            has_config = (repository_path / ".codeql.json").exists()
            
            result = len(project_dirs) > 1 or has_config
            self._logger.debug(f"Monorepo check for {repository_path}: {result} ({len(project_dirs)} project dirs)")
            return result
            
        except Exception as e:
            self._logger.error(f"Monorepo detection failed for {repository_path}: {e}")
            return False

    async def _has_project_indicators(self, directory_path: Path) -> bool:
        """Check if a directory has indicators of being a project."""
        try:
            # Common project indicators
            project_indicators = [
                # Build files
                "package.json", "pom.xml", "build.gradle", "Cargo.toml", "go.mod",
                "requirements.txt", "pyproject.toml", "setup.py", "Pipfile",
                "*.csproj", "*.sln", "Package.swift", "Gemfile",
                
                # Source directories
                "src/", "lib/", "app/", "source/", "Sources/",
                
                # Language-specific indicators
                "tsconfig.json", "webpack.config.js", "vite.config.js",
                "CMakeLists.txt", "Makefile", "configure.ac",
            ]
            
            for indicator in project_indicators:
                if "*" in indicator:
                    # Handle glob patterns
                    matches = list(directory_path.glob(indicator))
                    if matches:
                        return True
                elif indicator.endswith("/"):
                    # Handle directories
                    dir_path = directory_path / indicator.rstrip("/")
                    if dir_path.exists() and dir_path.is_dir():
                        return True
                else:
                    # Handle files
                    file_path = directory_path / indicator
                    if file_path.exists():
                        return True
            
            # If no specific indicators, check for source files
            source_extensions = ['.py', '.js', '.ts', '.java', '.cs', '.go', '.rs', '.swift', '.rb', '.cpp', '.c', '.h']
            for file_path in directory_path.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in source_extensions:
                    # Skip common non-project directories
                    skip_dirs = {'node_modules', '__pycache__', '.git', 'target', 'build', 'dist'}
                    if not any(skip_dir in str(file_path) for skip_dir in skip_dirs):
                        return True
            
            return False
            
        except Exception as e:
            self._logger.error(f"Project indicator check failed for {directory_path}: {e}")
            return False
