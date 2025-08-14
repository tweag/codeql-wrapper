"""Use case for running CodeQL analysis following v2 architecture patterns."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Set, List

from codeql_wrapper_v2.domain.entities.project import Project
from codeql_wrapper_v2.domain.enumerators.analysis_status import AnalysisStatus

from .....domain.entities.analyze_repository_request import AnalyzeRepositoryRequest
from .....domain.entities.analysis_result import ProjectAnalysisResult, RepositoryAnalysisResult
from .....domain.interfaces.analysis_service import AnalysisService
from .....domain.interfaces.codeql_service import CodeQLService
from .....domain.interfaces.project_detector import ProjectDetector
from .....domain.enumerators.language import Language
from .....domain.exceptions.analysis_exceptions import AnalysisError


class AnalyzeRepositoryUseCase:
    """Use case for analyzing repositories with CodeQL following v2 architecture."""
    
    def __init__(
        self,
        analysis_service: AnalysisService,
        logger: Optional[logging.Logger] = None
    ) -> None:
        """Initialize the use case with dependencies."""
        self._analysis_service = analysis_service
        self._logger = logger or logging.getLogger(__name__)
    
    async def execute(
        self,
        request: AnalyzeRepositoryRequest
    ) -> RepositoryAnalysisResult:
        """
        Execute codeql analysis on a list of projects.
                
        Args:
            request: AnalyzeRepositoryRequest containing analysis parameters
            
        Returns:
            RepositoryAnalysisResult with analysis summary
            
        Raises:
            AnalysisError: If analysis fails
        """
        try:    
            failed_projects: list[ProjectAnalysisResult] = []
            successful_projects: list[ProjectAnalysisResult] = []

            for project in request.projects:
                try:

                    self._logger.info(f"Analyzing project: {project.name} at {project.project_path}")

                    result = await self._analysis_service.analyze_project(project, request)
                    if result.status == AnalysisStatus.FAILED:
                        failed_projects.append(result)
                    else:
                        successful_projects.append(result)
                except Exception as e:
                    self._logger.error(f"Analysis failed for project {project.name}: {str(e)}")
                    failed_projects.append(ProjectAnalysisResult(
                        project=project,
                        error_message=str(e),
                        status=AnalysisStatus.FAILED
                    ))
                    continue

       
            usecase_result = RepositoryAnalysisResult(
                successful_projects=successful_projects,
                failed_projects=failed_projects
            )

            return usecase_result
            
        except Exception as e:
            self._logger.error(f"Repository analysis failed: {str(e)}")
            return RepositoryAnalysisResult(
                failed_projects = [],
                successful_projects = [],
                error_message=str(e)
            )
    