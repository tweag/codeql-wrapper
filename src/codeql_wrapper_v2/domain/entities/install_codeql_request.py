"""Domain entity for CodeQL installation request."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..exceptions.validation_exceptions import ValidationError


@dataclass(frozen=True)
class InstallCodeQLRequest:
    """Domain entity representing a CodeQL installation request."""
    
    version: Optional[str] = None
    force_reinstall: bool = False
    installation_directory: Optional[str] = None
    github_token: Optional[str] = None
    persistent_path: bool = True
    
    def __post_init__(self) -> None:
        """Validate the installation request."""
        self._validate_version()
        self._validate_installation_directory()
    
    def _validate_version(self) -> None:
        """Validate version format."""
        if not self.version:
            return
            
        version_pattern = r'^\d+\.\d+\.\d+(?:-\w+)?$'
        if not re.match(version_pattern, self.version):
            raise ValidationError(f"Invalid version format: {self.version}")
    
    def _validate_installation_directory(self) -> None:
        """Validate installation directory path."""
        if not self.installation_directory:
            return
            
        try:
            path = Path(self.installation_directory)
            if not path.is_absolute():
                raise ValidationError("Installation directory must be an absolute path")
        except Exception as e:
            raise ValidationError(f"Invalid installation directory: {e}")
    
    def is_latest_version_request(self) -> bool:
        """Check if this is a request for the latest version."""
        return self.version is None
    
    def requires_authentication(self) -> bool:
        """Check if this request includes GitHub authentication."""
        return self.github_token is not None
