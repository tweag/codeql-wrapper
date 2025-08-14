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
