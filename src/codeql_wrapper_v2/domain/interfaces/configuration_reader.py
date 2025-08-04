"""Interface for configuration file operations."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..entities.project import Project


class ConfigurationReader(ABC):
    """Abstract interface for reading project configuration files."""
    
    @abstractmethod
    async def read_config(self, config_file_path: Path) -> Dict[str, Any]:
        """
        Read configuration from a file.
        
        Args:
            config_file_path: Path to the configuration file
            
        Returns:
            Configuration data as dictionary
        """
        pass
    
    @abstractmethod
    async def validate_config(self, config_data: Dict[str, Any]) -> bool:
        """
        Validate configuration data structure.
        
        Args:
            config_data: Configuration data to validate
            
        Returns:
            True if configuration is valid
        """
        pass
    
    @abstractmethod
    async def parse_project_configs(self, config_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse individual project configurations from config data.
        
        Args:
            config_data: Full configuration data
            
        Returns:
            List of project configuration dictionaries
        """
        pass


class FileSystemAnalyzer(ABC):
    """Abstract interface for analyzing file system structure."""
    
    @abstractmethod
    async def get_subdirectories(self, directory_path: Path) -> List[Path]:
        """
        Get all subdirectories in a directory.
        
        Args:
            directory_path: Path to analyze
            
        Returns:
            List of subdirectory paths
        """
        pass
    
    @abstractmethod
    async def find_files_by_extension(self, directory_path: Path, extensions: List[str]) -> List[Path]:
        """
        Find files by extension in a directory (recursively).
        
        Args:
            directory_path: Directory to search
            extensions: List of file extensions to look for
            
        Returns:
            List of matching file paths
        """
        pass
    
    @abstractmethod
    async def has_files_matching_pattern(self, directory_path: Path, pattern: str) -> bool:
        """
        Check if directory contains files matching a pattern.
        
        Args:
            directory_path: Directory to search
            pattern: File pattern to match
            
        Returns:
            True if matching files are found
        """
        pass
