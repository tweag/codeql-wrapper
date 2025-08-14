"""Configuration file reader implementation."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from codeql_wrapper_v2.domain.interfaces.configuration_reader import ConfigurationReader


class JsonConfigurationReader(ConfigurationReader):
    """Implementation for reading JSON configuration files."""
    
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        """Initialize the configuration reader."""
        self._logger = logger or logging.getLogger(__name__)
    
    async def read_config(self, config_file_path: Path) -> Dict[str, Any]:
        """Read configuration from a JSON file."""
        try:
            with open(config_file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            self._logger.debug(f"Successfully read config from {config_file_path}")
            return config_data
            
        except json.JSONDecodeError as e:
            self._logger.error(f"Invalid JSON in config file {config_file_path}: {e}")
            raise ValueError(f"Invalid JSON in config file: {e}")
        
        except FileNotFoundError:
            self._logger.error(f"Config file not found: {config_file_path}")
            raise ValueError(f"Config file not found: {config_file_path}")
        
        except Exception as e:
            self._logger.error(f"Failed to read config file {config_file_path}: {e}")
            raise ValueError(f"Failed to read config file: {e}")
    
    async def validate_config(self, config_data: Dict[str, Any]) -> bool:
        """Validate CodeQL configuration data structure."""
        try:
            # Check for required top-level structure
            if not isinstance(config_data, dict):
                self._logger.error("Config must be a JSON object")
                return False
            
            # Check for projects array if present
            if "projects" in config_data:
                projects = config_data["projects"]
                if not isinstance(projects, list):
                    self._logger.error("'projects' must be an array")
                    return False
                
                # Validate each project configuration
                for i, project in enumerate(projects):
                    if not isinstance(project, dict):
                        self._logger.error(f"Project {i} must be an object")
                        return False
                    
                    # Check required fields
                    if "path" not in project:
                        self._logger.error(f"Project {i} missing required 'path' field")
                        return False
                    
                    # Validate optional fields
                    valid_fields = {
                        "path", "build-mode", "build-script", "query_pack", "language", "languages"
                    }
                    for field in project.keys():
                        if field not in valid_fields:
                            self._logger.warning(f"Project {i} has unknown field: {field}")
                    
                    # Validate build-mode values
                    if "build-mode" in project:
                        valid_build_modes = {"none", "manual", "autobuild"}
                        build_mode = project["build-mode"]
                        if build_mode not in valid_build_modes:
                            self._logger.error(
                                f"Project {i} has invalid build-mode: {build_mode}. "
                                f"Valid values: {valid_build_modes}"
                            )
                            return False
                    
                    # Validate queries is an array if present
                    if "queries" in project and not isinstance(project["queries"], list):
                        self._logger.error(f"Project {i} 'queries' must be an array")
                        return False
            
            self._logger.debug("Config validation passed")
            return True
            
        except Exception as e:
            self._logger.error(f"Config validation failed: {e}")
            return False
    
    async def parse_project_configs(self, config_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse individual project configurations from config data."""
        try:
            if "projects" not in config_data:
                self._logger.warning("No 'projects' array found in config")
                return []
            
            projects = config_data["projects"]
            if not isinstance(projects, list):
                self._logger.error("'projects' must be an array")
                return []
            
            # Validate config before returning
            is_valid = await self.validate_config(config_data)
            if not is_valid:
                self._logger.error("Config validation failed")
                return []
            
            self._logger.debug(f"Parsed {len(projects)} project configurations")
            return projects
            
        except Exception as e:
            self._logger.error(f"Failed to parse project configs: {e}")
            return []
