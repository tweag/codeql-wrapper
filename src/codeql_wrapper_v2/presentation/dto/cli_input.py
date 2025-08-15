"""Data Transfer Objects for CLI input handling."""

from dataclasses import dataclass
from typing import Optional
from pathlib import Path


@dataclass(frozen=True)
class InstallCommand:
    """Command input for CodeQL installation."""
    
    version: Optional[str] = None
    force_reinstall: bool = False
    installation_directory: Optional[str] = None
    github_token: Optional[str] = None
    persistent_path: bool = True
    quiet: bool = False
    verbose: bool = False
    
    def __post_init__(self) -> None:
        """Validate command input."""
        if self.installation_directory:
            # Validate that installation directory is a valid path
            try:
                Path(self.installation_directory).resolve()
            except (OSError, ValueError) as e:
                raise ValueError(f"Invalid installation directory: {e}")


@dataclass(frozen=True)
class DetectProjectsCommand:
    """Command input for project detection."""
    
    repository_path: str
    monorepo: bool = False
    languages: Optional[str] = None
    changed_files_only: bool = False
    base_ref: Optional[str] = None
    ref: Optional[str] = None
    config: Optional[str] = None
    quiet: bool = False
    verbose: bool = False
    
    def __post_init__(self) -> None:
        """Validate command input."""
        if self.repository_path:
            # Validate that repository path is a valid path
            try:
                path = Path(self.repository_path)
                if not path.exists():
                    raise ValueError(f"Repository path does not exist: {self.repository_path}")
                if not path.is_dir():
                    raise ValueError(f"Repository path is not a directory: {self.repository_path}")
            except (OSError, ValueError) as e:
                raise ValueError(f"Invalid repository path: {e}")
        
        if self.config:
            # Validate that config path is a valid file
            try:
                config_path = Path(self.config)
                if not config_path.exists():
                    raise ValueError(f"Configuration file does not exist: {self.config}")
                if not config_path.is_file():
                    raise ValueError(f"Configuration path is not a file: {self.config}")
            except (OSError, ValueError) as e:
                raise ValueError(f"Invalid configuration file: {e}")


@dataclass(frozen=True)
class AnalyzeCommand:
    """Command input for repository analysis."""
    
    repository_path: str
    languages: Optional[str] = None
    monorepo: bool = False
    changed_files_only: bool = False
    base_ref: Optional[str] = None
    ref: Optional[str] = None
    config: Optional[str] = None
    output_directory: Optional[str] = None
    verbose: bool = False
    quiet: bool = False
    
    def __post_init__(self) -> None:
        """Validate command input."""
        if self.repository_path:
            # Validate that repository path is a valid path
            try:
                path = Path(self.repository_path)
                if not path.exists():
                    raise ValueError(f"Repository path does not exist: {self.repository_path}")
                if not path.is_dir():
                    raise ValueError(f"Repository path is not a directory: {self.repository_path}")
            except (OSError, ValueError) as e:
                raise ValueError(f"Invalid repository path: {e}")
        
        if self.config:
            # Validate that config path is a valid file
            try:
                config_path = Path(self.config)
                if not config_path.exists():
                    raise ValueError(f"Configuration file does not exist: {self.config}")
                if not config_path.is_file():
                    raise ValueError(f"Configuration path is not a file: {self.config}")
            except (OSError, ValueError) as e:
                raise ValueError(f"Invalid configuration file: {e}")
        
        if self.output_directory:
            # Validate that output directory path is valid
            try:
                Path(self.output_directory).resolve()
            except (OSError, ValueError) as e:
                raise ValueError(f"Invalid output directory: {e}")
