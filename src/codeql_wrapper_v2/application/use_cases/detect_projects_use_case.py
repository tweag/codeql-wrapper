"""Use case for detecting projects within a repository."""

import logging
from pathlib import Path
from typing import List, Optional

from codeql_wrapper_v2.domain.entities.detect_projects_request import DetectProjectsRequest
from codeql_wrapper_v2.domain.entities.detect_projects_result import DetectProjectsResult
from codeql_wrapper_v2.domain.entities.project import Project
from codeql_wrapper_v2.domain.entities.repository import Repository
from codeql_wrapper_v2.domain.interfaces.project_detector import ProjectDetector, LanguageDetector
from codeql_wrapper_v2.domain.interfaces.configuration_reader import ConfigurationReader, FileSystemAnalyzer
from codeql_wrapper_v2.domain.services.project_detection_service import ProjectDetectionDomainService
from codeql_wrapper_v2.infrastructure.services.git_service import GitService

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
        
        # Initialize domain service
        self._domain_service = ProjectDetectionDomainService(
            language_detector=language_detector,
            config_reader=config_reader,
            file_system_analyzer=file_system_analyzer,
            logger=logger
        )
        
        # Initialize Git service
        self._git_service: Optional[GitService] = None
    
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
            
            # Initialize Git service if needed for change detection
            if request.should_filter_by_changes():
                self._git_service = GitService(request.repository_path, self._logger)
            
            # Use domain service to detect projects (language filtering included)
            result = await self._domain_service.detect_projects(request)
            
            # Apply Git-based filtering at application layer
            if request.should_filter_by_changes() and result.is_successful():
                filtered_projects = await self._filter_projects_by_changes(
                    result.detected_projects, request
                )
                
                # Update result with filtered projects
                result = DetectProjectsResult(
                    repository=result.repository,
                    detected_projects=filtered_projects,
                    is_monorepo=len(filtered_projects) > 1,
                    config_file_used=result.config_file_used
                )
            
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
    
    async def _filter_projects_by_changes(
        self, 
        projects: List[Project], 
        request: DetectProjectsRequest
    ) -> List[Project]:
        """Filter projects based on changed files using Git."""
        if not self._git_service:
            return projects
        
        try:
            # Get changed files using Git service
            changed_files = self._git_service.get_changed_files(
                base_ref=request.base_ref,
                current_ref=request.ref
            )
            
            self._logger.info(f"Detected {len(changed_files)} changed files using Git references")
            
            # Filter projects that have changed files
            filtered_projects = [
                project for project in projects
                if await self._project_has_changed_files(project, changed_files)
            ]
            
            return filtered_projects
            
        except Exception as e:
            self._logger.warning(f"Error filtering projects by changes: {e}")
            return projects
    
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

