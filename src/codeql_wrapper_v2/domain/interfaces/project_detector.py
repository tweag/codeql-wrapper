"""Interface for project detection within repositories."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Set

from ..entities.detect_projects_request import DetectProjectsRequest
from ..entities.detect_projects_result import DetectProjectsResult
from ..entities.project import Project
from ..entities.repository import Repository
from ..enumerators.language import Language


class ProjectDetector(ABC):
    """Abstract interface for detecting projects within a repository."""
    
    @abstractmethod
    async def detect_projects(self, request: DetectProjectsRequest) -> DetectProjectsResult:
        """
        Detect all projects within a repository based on the request parameters.
        
        Args:
            request: Project detection request with all parameters
            
        Returns:
            DetectProjectsResult containing detected projects and metadata
        """
        pass
    
    @abstractmethod
    async def is_monorepo(self, repository_path: Path) -> bool:
        """
        Determine if repository follows monorepo structure.
        
        Args:
            repository_path: Path to the repository root
            
        Returns:
            True if repository contains multiple projects
        """
        pass
    
    @abstractmethod
    async def validate_project_structure(self, project_path: Path) -> bool:
        """
        Validate that a path contains a valid project structure.
        
        Args:
            project_path: Path to potential project
            
        Returns:
            True if path contains a valid project
        """
        pass


class LanguageDetector(ABC):
    """Abstract interface for detecting programming languages in projects."""
    
    @abstractmethod
    async def detect_languages(self, project_path: Path) -> Set[Language]:
        """
        Detect programming languages in a project directory.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Set of detected languages
        """
        pass
    
    @abstractmethod
    async def detect_primary_language(self, project_path: Path) -> Language:
        """
        Detect the primary programming language in a project.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Primary language detected
        """
        pass