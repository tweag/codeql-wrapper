"""Command for installing CodeQL CLI."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class InstallCodeQLCommand:
    """Command to install CodeQL CLI."""
    
    version: Optional[str] = None
    force_reinstall: bool = False
    installation_directory: Optional[str] = None
    github_token: Optional[str] = None
    persistent_path: bool = True
    quiet: bool = False
    verbose: bool = False
    
    def __post_init__(self) -> None:
        """Validate command input."""
        self._validate_installation_directory()
        self._validate_version_format()
    
    def _validate_installation_directory(self) -> None:
        """Validate installation directory if provided."""
        if not self.installation_directory:
            return
            
        try:
            path = Path(self.installation_directory)
            # Check if parent directory exists
            if not path.parent.exists():
                raise ValueError(f"Parent directory does not exist: {path.parent}")
        except (OSError, ValueError) as e:
            raise ValueError(f"Invalid installation directory: {e}")
    
    def _validate_version_format(self) -> None:
        """Validate version format if provided."""
        if not self.version:
            return
            
        # Basic version validation (semantic versioning)
        version_pattern = r'^\d+\.\d+\.\d+(?:-\w+)?$'
        if not re.match(version_pattern, self.version):
            raise ValueError(f"Invalid version format: {self.version}. Expected format: X.Y.Z")
