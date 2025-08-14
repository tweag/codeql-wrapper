"""Domain entity for analyze repository requests."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Set

from codeql_wrapper_v2.domain.entities.project import Project

from ..enumerators.language import Language


@dataclass(frozen=True)
class AnalyzeRepositoryRequest:
    """Domain request for analyzing a repository."""
    
    projects: List[Project]
    output_directory: Path 
   