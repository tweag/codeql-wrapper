"""Request entity for detecting projects within a repository."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from ..enumerators.language import Language


@dataclass(frozen=True)
class DetectProjectsRequest:
    """Request to detect projects within a repository."""
    
    repository_path: Path
    is_monorepo: bool = False
    target_languages: Optional[List[Language]] = None
    include_changed_files_only: bool = False
    changed_files: Optional[List[str]] = None
    config_file_path: Optional[Path] = None
    
    def __post_init__(self) -> None:
        """Validate request parameters."""
        if not self.repository_path.exists():
            raise ValueError(f"Repository path does not exist: {self.repository_path}")
        
        if not self.repository_path.is_dir():
            raise ValueError(f"Repository path is not a directory: {self.repository_path}")
        
        # Note: changed_files will be auto-detected when include_changed_files_only is True
        
        if self.config_file_path and not self.config_file_path.exists():
            raise ValueError(f"Config file does not exist: {self.config_file_path}")
    
    def should_filter_by_language(self) -> bool:
        """Check if detection should be filtered by specific languages."""
        return self.target_languages is not None and len(self.target_languages) > 0
    
    def should_filter_by_changes(self) -> bool:
        """Check if detection should be filtered by changed files."""
        return self.include_changed_files_only
    
    def has_config_file(self) -> bool:
        """Check if a configuration file is provided."""
        return self.config_file_path is not None
    
    def get_config_file_path(self) -> Optional[Path]:
        """Get the configuration file path, or search for .codeql.json recursively."""
        if self.config_file_path:
            return self.config_file_path
        
        # First check the repository root
        default_config = self.repository_path / ".codeql.json"
        if default_config.exists():
            return default_config
        
        # Search recursively for .codeql.json files
        try:
            for config_file in self.repository_path.rglob(".codeql.json"):
                if config_file.is_file():
                    return config_file
        except Exception:
            # If search fails, return None
            pass
        
        return None
