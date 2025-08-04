"""File system analyzer implementation."""

import fnmatch
import logging
from pathlib import Path
from typing import List, Optional

from codeql_wrapper_v2.domain.interfaces.configuration_reader import FileSystemAnalyzer


class FileSystemAnalyzerImpl(FileSystemAnalyzer):
    """Implementation of file system analysis operations."""
    
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        """Initialize the file system analyzer."""
        self._logger = logger or logging.getLogger(__name__)
    
    async def get_subdirectories(self, directory_path: Path) -> List[Path]:
        """Get all subdirectories in a directory."""
        try:
            subdirs = []
            for item in directory_path.iterdir():
                if item.is_dir():
                    subdirs.append(item)
            return subdirs
        except Exception as e:
            self._logger.error(f"Failed to list subdirectories in {directory_path}: {e}")
            return []
    
    async def find_files_by_extension(self, directory_path: Path, extensions: List[str]) -> List[Path]:
        """Find files by extension in a directory (recursively)."""
        try:
            files = []
            
            # Normalize extensions
            normalized_extensions = []
            for ext in extensions:
                if not ext.startswith('.'):
                    ext = f'.{ext}'
                normalized_extensions.append(ext.lower())
            
            # Search recursively
            for file_path in directory_path.rglob('*'):
                if (file_path.is_file() and 
                    file_path.suffix.lower() in normalized_extensions):
                    files.append(file_path)
            
            return files
            
        except Exception as e:
            self._logger.error(f"Failed to find files by extension in {directory_path}: {e}")
            return []
    
    async def has_files_matching_pattern(self, directory_path: Path, pattern: str) -> bool:
        """Check if directory contains files matching a pattern."""
        try:
            for file_path in directory_path.rglob('*'):
                if file_path.is_file() and fnmatch.fnmatch(file_path.name, pattern):
                    return True
            return False
            
        except Exception as e:
            self._logger.error(f"Failed to search for pattern {pattern} in {directory_path}: {e}")
            return False
