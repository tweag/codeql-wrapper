"""Repository entity for CodeQL analysis domain."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .project import Project


@dataclass(frozen=True)
class Repository:
    """Represents a code repository containing one or more projects."""
    
    path: Path
    name: Optional[str] = None
    is_git_repository: bool = False
    
    def __post_init__(self) -> None:
        """Validate repository state on creation."""
        if not self.path.exists():
            raise ValueError(f"Repository path does not exist: {self.path}")
        
        if not self.path.is_dir():
            raise ValueError(f"Repository path is not a directory: {self.path}")
        
        # Set name if not provided
        if self.name is None:
            object.__setattr__(self, 'name', self.path.name or self.path.resolve().name)
    
    def get_git_directory(self) -> Optional[Path]:
        """Get the .git directory if this is a git repository."""
        git_dir = self.path / ".git"
        return git_dir if git_dir.exists() else None
    
    def is_monorepo(self, projects: List[Project]) -> bool:
        """Determine if this repository is a monorepo based on detected projects."""
        return len(projects) > 1
    
    def has_codeql_config(self) -> bool:
        """Check if repository has a .codeql.json configuration file."""
        return (self.path / ".codeql.json").exists()
    
    def get_codeql_config_path(self) -> Optional[Path]:
        """Get path to .codeql.json configuration file if it exists."""
        config_path = self.path / ".codeql.json"
        return config_path if config_path.exists() else None
    
    def get_display_name(self) -> str:
        """Get a display-friendly name for the repository."""
        return self.name or "Unknown Repository"
