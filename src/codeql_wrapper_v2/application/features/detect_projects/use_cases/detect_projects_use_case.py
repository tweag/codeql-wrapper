"""Use case for detecting projects within a repository."""

import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Set, Any

from codeql_wrapper_v2.domain.entities.detect_projects_request import DetectProjectsRequest
from codeql_wrapper_v2.domain.entities.detect_projects_result import DetectProjectsResult
from codeql_wrapper_v2.domain.entities.project import Project
from codeql_wrapper_v2.domain.entities.repository import Repository
from codeql_wrapper_v2.domain.enumerators.language import Language
from codeql_wrapper_v2.domain.interfaces.project_detector import ProjectDetector, LanguageDetector
from codeql_wrapper_v2.domain.interfaces.configuration_reader import ConfigurationReader, FileSystemAnalyzer

class DetectProjectsUseCase:
    """Use case for detecting projects within a repository."""
    
    def __init__(
        self,
        project_detector: ProjectDetector,
        language_detector: LanguageDetector,
        config_reader: ConfigurationReader,
        file_system_analyzer: FileSystemAnalyzer,
        logger: Optional[logging.Logger] = None
    ) -> None:
        """Initialize the use case with its dependencies."""
        self._project_detector = project_detector
        self._language_detector = language_detector
        self._config_reader = config_reader
        self._file_system_analyzer = file_system_analyzer
        self._logger = logger or logging.getLogger(__name__)
    
    async def execute(self, request: DetectProjectsRequest) -> DetectProjectsResult:
        """
        Execute project detection based on the request.
        
        Args:
            request: Domain request containing detection parameters
            
        Returns:
            DetectProjectsResult with detected projects
        """
        try:
            self._logger.info(f"Starting project detection in: {request.repository_path}")
            
            # Create repository entity
            repository = Repository(
                path=request.repository_path,
                is_git_repository=self._is_git_repository(request.repository_path)
            )
            
            # Detect projects using the domain service
            result = await self._project_detector.detect_projects(request)
            
            self._logger.info(f"Detection completed: {result.get_summary()}")
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
    
    def _is_git_repository(self, repository_path: Path) -> bool:
        """Check if the path is a git repository."""
        return (repository_path / ".git").exists()


class ProjectDetectionService:
    """Service implementing the project detection domain logic."""
    
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
            if request.is_monorepo:
                projects = await self._detect_monorepo_projects(request, config_data)
            else:
                projects = await self._detect_single_project(request)
            
            # Filter projects based on request criteria
            filtered_projects = await self._filter_projects(projects, request)
            
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
    
    async def _filter_projects(self, projects: List[Project], request: DetectProjectsRequest) -> List[Project]:
        """Filter projects based on request criteria."""
        filtered_projects = projects
        
        # Filter by target languages
        if request.should_filter_by_language():
            target_languages = set(request.target_languages or [])
            filtered_projects = [
                project for project in filtered_projects
                if target_languages.intersection(project.detected_languages)
            ]
        
        # Filter by changed files
        if request.should_filter_by_changes():
            # Auto-detect changed files if not provided
            changed_files = request.changed_files
            if not changed_files and request.include_changed_files_only:
                changed_files = await self._detect_changed_files(request.repository_path)
                self._logger.info(f"Auto-detected {len(changed_files)} changed files")
            
            filtered_projects = [
                project for project in filtered_projects
                if await self._project_has_changed_files(project, changed_files or [])
            ]
        
        return filtered_projects
    
    async def _detect_changed_files(self, repository_path: Path) -> List[str]:
        """Auto-detect changed files using git."""
        try:
            # Get changed files using git diff
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                cwd=repository_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            changed_files = [f.strip() for f in result.stdout.split('\n') if f.strip()]
            
            # Also get staged files
            staged_result = subprocess.run(
                ["git", "diff", "--name-only", "--cached"],
                cwd=repository_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            staged_files = [f.strip() for f in staged_result.stdout.split('\n') if f.strip()]
            
            # Combine and deduplicate
            all_changed_files = list(set(changed_files + staged_files))
            
            self._logger.debug(f"Detected changed files: {all_changed_files}")
            return all_changed_files
            
        except subprocess.CalledProcessError as e:
            self._logger.warning(f"Failed to detect changed files using git: {e}")
            return []
        except Exception as e:
            self._logger.warning(f"Error detecting changed files: {e}")
            return []
    
    async def _project_has_changed_files(self, project: Project, changed_files: List[str]) -> bool:
        """Check if a project contains any of the changed files."""
        if not changed_files:
            return False
        
        try:
            relative_project_path = project.get_relative_path()
            project_prefix = str(relative_project_path)
        except ValueError:
            return False
        
        # Normalize project prefix
        project_prefix = project_prefix.rstrip("/")
        
        # Check if any changed file is within this project
        for changed_file in changed_files:
            changed_file = changed_file.rstrip("/")
            
            # Root project matches all files
            if project_prefix == "." or project_prefix == "":
                return True
            
            # Check if file is within project directory
            if (
                changed_file.startswith(f"{project_prefix}/") or 
                changed_file == project_prefix
            ):
                return True
        
        return False
