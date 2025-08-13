"""Command for running CodeQL analysis."""

from dataclasses import dataclass
from typing import Optional, Set
from pathlib import Path


@dataclass(frozen=True)
class RunAnalysisCommand:
    """Command to run CodeQL analysis on a repository."""
    
    repository_path: str
    languages: Optional[Set[str]] = None
    output_directory: Optional[str] = None
    monorepo: bool = False
    verbose: bool = False
    force_install: bool = False
    max_workers: Optional[int] = None
    only_changed_files: bool = False
    base_ref: Optional[str] = None
    current_ref: Optional[str] = None
    upload_sarif: bool = False
    github_token: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Validate command parameters."""
        # Validate repository path exists
        repo_path = Path(self.repository_path)
        if not repo_path.exists():
            raise ValueError(f"Repository path does not exist: {self.repository_path}")
        
        if not repo_path.is_dir():
            raise ValueError(f"Repository path must be a directory: {self.repository_path}")
        
        # Validate max_workers if provided
        if self.max_workers is not None and self.max_workers <= 0:
            raise ValueError("max_workers must be greater than 0")
            
        # Validate upload requirements
        if self.upload_sarif and not self.github_token:
            raise ValueError("github_token is required when upload_sarif is True")
