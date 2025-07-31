"""Interface for project detection within repositories."""

from abc import ABC, abstractmethod
from typing import List
from ..entities.project import Project
from ..entities.repository import Repository


class ProjectDetector(ABC):
    """Abstract interface for detecting projects within a repository."""
    
    @abstractmethod
    async def detect_projects(self, repository_path: str) -> List[Project]:
        """
        Detect all projects within a repository.
        
        Args:
            repository_path: Path to the repository root
            
        Returns:
            List of detected projects with their metadata
        """
        pass
    
    @abstractmethod
    async def is_monorepo(self, repository_path: str) -> bool:
        """
        Determine if repository follows monorepo structure.
        
        Args:
            repository_path: Path to the repository root
            
        Returns:
            True if repository contains multiple projects
        """
        pass
    
    @abstractmethod
    async def validate_project_structure(self, project_path: str) -> bool:
        """
        Validate that a path contains a valid project structure.
        
        Args:
            project_path: Path to potential project
            
        Returns:
            True if path contains a valid project
        """
        pass