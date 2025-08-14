"""Domain interface for repository analysis service."""

from abc import ABC, abstractmethod
from typing import Protocol

from codeql_wrapper_v2.domain.entities.project import Project

from ..entities.analyze_repository_request import AnalyzeRepositoryRequest
from ..entities.analysis_result import ProjectAnalysisResult, RepositoryAnalysisResult


class AnalysisService(Protocol):
    """Domain service interface for repository analysis operations."""
    
    @abstractmethod
    async def analyze_project(self, project: Project, request: AnalyzeRepositoryRequest) -> ProjectAnalysisResult:
        """
        Analyze a project with CodeQL.
        
        Args:
            request: Domain request containing analysis parameters
            
        Returns:
            ProjectAnalysisResult with analysis results

        Raises:
            AnalysisError: If analysis fails
        """
        pass
