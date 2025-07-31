"""Operating system operations abstraction for CodeQL wrapper."""

import os
import platform
import re
import shutil
import stat
from pathlib import Path
from typing import Dict, Optional, Tuple

from ..exceptions.os_exceptions import FileSystemError, PermissionError, EnvironmentError


class OSOperations:
    """
    Abstraction layer for operating system operations.
    
    Handles file system operations, environment variables, and platform-specific logic
    in a clean, testable way following Clean Architecture principles.
    """
    
    def __init__(self) -> None:
        """Initialize OS operations handler."""
        self._platform_info = self._detect_platform()
    
    def get_platform_info(self) -> Dict[str, str]:
        """Get cached platform information."""
        return self._platform_info.copy()
    
    def get_default_installation_directory(self, application_name: str) -> str:
        """
        Get default installation directory based on platform.
        
        Args:
            application_name: Name of the application for directory creation
            
        Returns:
            Platform-appropriate installation directory path
        """
        system = self._platform_info["system"]
        
        if system == "windows":
            # Windows: %LOCALAPPDATA%\{ApplicationName}
            local_app_data = os.environ.get("LOCALAPPDATA")
            if local_app_data:
                return os.path.join(local_app_data, application_name)
            else:
                return os.path.join(os.path.expanduser("~"), "AppData", "Local", application_name)
                
        elif system == "darwin":
            # macOS: ~/Library/Application Support/{ApplicationName}
            return os.path.join(os.path.expanduser("~"), "Library", "Application Support", application_name)
            
        else:
            # Linux and others: ~/.local/share/{application_name_lowercase}
            app_name_lower = application_name.lower()
            return os.path.join(os.path.expanduser("~"), ".local", "share", app_name_lower)
    
    def create_directory(self, path: Path, parents: bool = True, exist_ok: bool = True) -> None:
        """Create directory with proper error handling."""
        try:
            path.mkdir(parents=parents, exist_ok=exist_ok)
        except OSError as e:
            raise FileSystemError(f"Failed to create directory {path}: {e}", operation="create_directory", path=str(path))
    
    def remove_directory(self, path: Path) -> None:
        """Remove directory tree with proper error handling."""
        try:
            if path.exists():
                shutil.rmtree(path)
        except OSError as e:
            raise FileSystemError(f"Failed to remove directory {path}: {e}", operation="remove_directory", path=str(path))
    
    def set_executable_permissions(self, file_path: Path) -> None:
        """Set executable permissions on a file."""
        try:
            current_mode = file_path.stat().st_mode
            new_mode = current_mode | stat.S_IEXEC | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
            file_path.chmod(new_mode)
        except OSError as e:
            raise PermissionError(f"Failed to set executable permissions on {file_path}: {e}", operation="set_executable", path=str(file_path))
    
    def is_executable(self, file_path: Path) -> bool:
        """Check if file has executable permissions."""
        return file_path.exists() and os.access(file_path, os.X_OK)
    
    def get_environment_variable(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get environment variable value."""
        return os.environ.get(name, default)
    
    def set_environment_variable(self, name: str, value: str) -> None:
        """Set environment variable for current session."""
        os.environ[name] = value
    
    def get_current_path(self) -> str:
        """Get current PATH environment variable."""
        return os.environ.get("PATH", "")
    
    def add_to_current_path(self, directory: str) -> None:
        """Add directory to PATH for current session."""
        current_path = self.get_current_path()
        if directory not in current_path:
            os.environ["PATH"] = f"{directory}{os.pathsep}{current_path}"
    
    def expand_user_path(self, path: str) -> str:
        """Expand user home directory in path."""
        return os.path.expanduser(path)
    
    def make_path_persistent_windows(self, directory: str) -> bool:
        """
        Make PATH persistent on Windows by modifying user environment variables.
        
        Returns:
            True if directory was added, False if already present
        """
        try:
            import winreg  # type: ignore
            
            # Open user environment variables registry key
            with winreg.OpenKey(  # type: ignore
                winreg.HKEY_CURRENT_USER,  # type: ignore
                "Environment",
                0,
                winreg.KEY_ALL_ACCESS  # type: ignore
            ) as key:
                try:
                    # Get current PATH value
                    current_path, _ = winreg.QueryValueEx(key, "PATH")  # type: ignore
                except FileNotFoundError:
                    current_path = ""
                
                # Add directory to PATH if not already present
                if directory not in current_path:
                    new_path = f"{directory};{current_path}" if current_path else directory
                    winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)  # type: ignore
                    return True
                else:
                    return False  # Already present
                    
        except ImportError:
            raise EnvironmentError("winreg module not available (not on Windows)", operation="windows_path_persistence")
        except Exception as e:
            raise EnvironmentError(f"Failed to modify Windows registry: {e}", operation="windows_path_persistence")
    
    def make_path_persistent_unix(self, directory: str) -> Tuple[bool, str]:
        """
        Make PATH persistent on Unix-like systems by modifying shell profile.
        
        Returns:
            Tuple of (success, target_profile_path)
        """
        target_profile = self._find_target_shell_profile()
        
        if self._is_already_in_profile(directory, target_profile):
            return False, target_profile  # Already present
        
        self._add_to_shell_profile(directory, target_profile)
        return True, target_profile
    
    def _detect_platform(self) -> Dict[str, str]:
        """Detect current platform information for CodeQL binary selection."""
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        # Map Python's platform detection to CodeQL's naming convention
        os_mapping = {
            "windows": "win64",
            "darwin": "osx64", 
            "linux": "linux64"
        }
        
        # Map architecture
        arch_mapping = {
            "x86_64": "64",
            "amd64": "64", 
            "arm64": "64",  #  binaries are typically x64 even on ARM Macs
            "aarch64": "64"
        }
        
        detected_os = os_mapping.get(system, "linux64")
        detected_arch = arch_mapping.get(machine, "64")
        
        # For macOS ARM (M1/M2), we still use osx64 as CodeQL provides universal binaries
        if system == "darwin" and machine in ["arm64", "aarch64"]:
            detected_os = "osx64"
            
        return {
            "os": detected_os,
            "arch": detected_arch,
            "system": system,
            "machine": machine
        }
    
    def _find_target_shell_profile(self) -> str:
        """Find the most appropriate shell profile file to modify."""
        home_dir = self.expand_user_path("~")
        
        # Check for common shells and their profile files
        shell_profiles = {
            "bash": [".bashrc", ".bash_profile", ".profile"],
            "zsh": [".zshrc", ".zprofile"],
            "fish": [".config/fish/config.fish"],
        }
        
        # Try to detect current shell
        shell_env = self.get_environment_variable("SHELL", "")
        current_shell = shell_env.split("/")[-1] if shell_env else ""
        profile_files = []
        
        if current_shell in shell_profiles:
            profile_files.extend(shell_profiles[current_shell])
        else:
            # Default to common profile files
            profile_files.extend([".bashrc", ".zshrc", ".profile"])
        
        # Look for existing profile files
        for profile in profile_files:
            profile_path = os.path.join(home_dir, profile)
            if os.path.exists(profile_path):
                return profile_path
        
        # If no existing profiles, create .profile as fallback
        return os.path.join(home_dir, ".profile")
    
    def _is_already_in_profile(self, directory: str, target_profile: str) -> bool:
        """Check if directory is already in the profile file."""
        path_pattern = re.escape(directory)
        
        try:
            with open(target_profile, 'r', encoding='utf-8') as f:
                content = f.read()
                return bool(re.search(path_pattern, content))
        except FileNotFoundError:
            return False
    
    def _add_to_shell_profile(self, directory: str, target_profile: str) -> None:
        """Add directory to shell profile file."""
        export_line = f'export PATH="{directory}:$PATH"'
        
        try:
            with open(target_profile, 'a', encoding='utf-8') as f:
                f.write(f"\n# Added by CodeQL Wrapper\n")
                f.write(f"{export_line}\n")
        except Exception as e:
            raise FileSystemError(f"Failed to modify {target_profile}: {e}", operation="modify_shell_profile", path=target_profile)
