"""Domain service for project detection logic."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..entities.detect_projects_request import DetectProjectsRequest
from ..entities.detect_projects_result import DetectProjectsResult
from ..entities.project import Project
from ..entities.repository import Repository
from ..enumerators.language import Language
from ..interfaces.project_detector import LanguageDetector
from ..interfaces.configuration_reader import ConfigurationReader, FileSystemAnalyzer


class ProjectDetectionDomainService:
    """Domain service implementing the core project detection business logic."""
    
    def __init__(
        self,
        language_detector: LanguageDetector,
        config_reader: ConfigurationReader,
        file_system_analyzer: FileSystemAnalyzer,
        logger: Optional[logging.Logger] = None
    ) -> None:
        """Initialize the service with its dependencies."""
        self._language_detector = language_detector
        self._config_reader = config_reader
        self._file_system_analyzer = file_system_analyzer
        self._logger = logger or logging.getLogger(__name__)
    
    async def detect_projects(self, request: DetectProjectsRequest) -> DetectProjectsResult:
        """
        Detect projects based on the request parameters.
        
        Args:
            request: Project detection request
            
        Returns:
            DetectProjectsResult with all detected projects
        """
        try:
            repository = Repository(
                path=request.repository_path,
                is_git_repository=(request.repository_path / ".git").exists()
            )
            
            # Check for configuration file
            config_file_path = request.get_config_file_path()
            config_data = None
            config_file_used = None
            
            if config_file_path:
                self._logger.info(f"Using configuration file: {config_file_path}")
                config_data = await self._config_reader.read_config(config_file_path)
                config_file_used = str(config_file_path.name)
            
            # Detect projects
            if request.is_monorepo or config_data:
                projects = await self._detect_monorepo_projects(request, config_data)
            else:
                projects = await self._detect_single_project(request)
            
            # Filter projects based on request criteria (but not by changed files here)
            filtered_projects = await self._filter_projects_by_language(projects, request)
            
            is_monorepo = len(filtered_projects) > 1
            
            return DetectProjectsResult(
                repository=repository,
                detected_projects=filtered_projects,
                is_monorepo=is_monorepo,
                config_file_used=config_file_used
            )
            
        except Exception as e:
            self._logger.error(f"Project detection failed: {e}")
            repository = Repository(path=request.repository_path)
            return DetectProjectsResult(
                repository=repository,
                detected_projects=[],
                is_monorepo=False,
                error_message=str(e)
            )
    
    async def _detect_monorepo_projects(
        self, 
        request: DetectProjectsRequest, 
        config_data: Optional[Dict[str, Any]]
    ) -> List[Project]:
        """Detect projects in a monorepo."""
        projects = []
        
        if config_data:
            # Use configuration-based detection
            project_configs = await self._config_reader.parse_project_configs(config_data)
            for project_config in project_configs:
                project = await self._create_project_from_config(request, project_config)
                if project:
                    projects.append(project)
        else:
            # Use directory-based detection
            subdirectories = await self._file_system_analyzer.get_subdirectories(request.repository_path)
            for subdir in subdirectories:
                if await self._is_valid_project_directory(subdir):
                    project = await self._create_project_from_directory(request, subdir)
                    if project:
                        projects.append(project)
        
        return projects
    
    async def _detect_single_project(self, request: DetectProjectsRequest) -> List[Project]:
        """Detect a single project in the repository root."""
        project = await self._create_project_from_directory(request, request.repository_path)
        return [project] if project else []
    
    async def _create_project_from_config(
        self, 
        request: DetectProjectsRequest, 
        config: Dict[str, Any]
    ) -> Optional[Project]:
        """Create a project from configuration data."""
        project_path = request.repository_path / config.get("path", "")
        
        if not project_path.exists():
            self._logger.warning(f"Project path does not exist: {project_path}")
            return None
        
        # Detect languages
        detected_languages = await self._language_detector.detect_languages(project_path)
        
        if not detected_languages:
            self._logger.debug(f"No languages detected in: {project_path}")
            return None
        
        # Parse target language from config
        target_language = None
        if config.get("language"):
            target_langs = Language.from_codeql_identifier(config["language"])
            target_language = target_langs[0] if target_langs else None
        
        # Build script path
        build_script_path = None
        if config.get("build-script"):
            build_script_path = request.repository_path / config["build-script"]
        
        return Project(
            name=project_path.name,
            project_path=project_path,
            repository_path=request.repository_path,
            detected_languages=detected_languages,
            target_language=target_language,
            build_mode=config.get("build-mode", "none"),
            build_script_path=build_script_path,
            queries=config.get("queries", [])
        )
    
    async def _create_project_from_directory(
        self, 
        request: DetectProjectsRequest, 
        project_path: Path
    ) -> Optional[Project]:
        """Create a project from a directory path."""
        # Detect languages
        detected_languages = await self._language_detector.detect_languages(project_path)
        
        if not detected_languages:
            self._logger.debug(f"No languages detected in: {project_path}")
            return None
        
        # Get project name - use directory name or "root" if empty
        project_name = project_path.name or "root"
        if not project_name or project_name == ".":
            project_name = "root"
        
        return Project(
            name=project_name,
            project_path=project_path,
            repository_path=request.repository_path,
            detected_languages=detected_languages
        )
    
    async def _is_valid_project_directory(self, directory_path: Path) -> bool:
        """Check if a directory contains a valid project."""
        # Skip hidden directories and common non-project directories
        skip_dirs = {".git", ".github", ".vscode", "node_modules", "__pycache__", ".pytest_cache", "target", "build", "dist"}
        
        if directory_path.name.startswith(".") or directory_path.name in skip_dirs:
            return False
        
        # Check for any programming language files
        detected_languages = await self._language_detector.detect_languages(directory_path)
        return len(detected_languages) > 0
    
    async def _filter_projects_by_language(self, projects: List[Project], request: DetectProjectsRequest) -> List[Project]:
        """Filter projects by target languages and update detected_languages to only include filtered languages."""
        filtered_projects = projects
        
        # Filter by target languages
        if request.should_filter_by_language():
            target_languages = set(request.target_languages or [])
            filtered_projects = []
            
            for project in projects:
                # Find intersection of detected languages and target languages
                matching_languages = target_languages.intersection(project.detected_languages)
                
                if matching_languages:
                    # Create a new project with only the matching languages
                    filtered_project = Project(
                        name=project.name,
                        project_path=project.project_path,
                        repository_path=project.repository_path,
                        detected_languages=matching_languages,  # Keep as set of matching languages
                        target_language=project.target_language if project.target_language in matching_languages else None,
                        build_mode=project.build_mode,
                        build_script_path=project.build_script_path,
                        queries=project.queries
                    )
                    filtered_projects.append(filtered_project)
        
        return filtered_projects
