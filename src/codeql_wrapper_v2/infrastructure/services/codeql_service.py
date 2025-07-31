"""
Infrastructure implementation of CodeQL service.

This module provides the concrete implementation of the CodeQL service interface,
handling all CodeQL CLI operations, installation management, and command execution.
"""

import json
import logging
import os
import re
import tempfile
import tarfile
import zipfile
from pathlib import Path
from typing import List, Optional, Dict, Any
import aiohttp

from ...domain.interfaces.codeql_service import (
    CodeQLService,
    CodeQLInstallationInfo,
    CodeQLExecutionResult,
)
from ...domain.exceptions.codeql_exceptions import (
    CodeQLError,
    CodeQLNotInstalledError,
    CodeQLInstallationError,
    CodeQLExecutionError,
)
from ...domain.constants.codeql_constants import CodeQLConstants
from ..external_tools.codeql_wrapper import CodeQLCLI
from ..file_system.os_operations import OSOperations
from ..exceptions.os_exceptions import FileSystemError, PermissionError, EnvironmentError


class CodeQLServiceImpl(CodeQLService):
    """
    Infrastructure implementation of CodeQL service interface.
    
    Provides concrete implementation for CodeQL CLI operations including:
    - Installation and version management
    - Command execution and result parsing
    - Error handling and logging
    - Platform-specific adaptations
    """
    
    def __init__(
        self,
        installation_directory: Optional[str] = None,
        github_token: Optional[str] = None,
        executable_path: Optional[str] = None,
    ) -> None:
        """
        Initialize CodeQL service implementation.
        
        Args:
            installation_directory: Custom directory for CodeQL installation
            github_token: GitHub token for API access (rate limiting)
            executable_path: Custom path to existing CodeQL executable
        """
        self._logger = logging.getLogger(__name__)
        self._os_operations = OSOperations()
        self._installation_directory = installation_directory or self._os_operations.get_default_installation_directory(CodeQLConstants.APPLICATION_NAME)
        self._github_token = github_token
        self._executable_path = executable_path
        self._codeql_cli: Optional[CodeQLCLI] = None
        
        # GitHub API configuration
        self._github_api_base_url = CodeQLConstants.GITHUB_API_BASE_URL
        self._github_releases_url = f"{self._github_api_base_url}/repos/github/codeql-cli-binaries/releases"
        
        # Platform-specific configuration
        self._platform_info = self._os_operations.get_platform_info()
        
    async def validate_installation(self) -> CodeQLInstallationInfo:
        """
        Validate CodeQL CLI installation and version.
        
        Returns:
            Installation information including version and upgrade availability
        """
        self._logger.info("Validating CodeQL installation")
        
        try:
            # Try to execute 'codeql --version' to check installation
            result = await self.execute_command(["--version"])
            
            if not result.success:
                self._logger.warning("CodeQL CLI not found or not accessible")
                return CodeQLInstallationInfo(
                    is_installed=False,
                    version=None,
                    installation_path=None,
                    is_latest_version=False,
                    available_latest_version=None
                )
            
            # Parse version and installation path from output
            current_version = self._parse_version_string(result.stdout)
            installation_path = self._parse_installation_path(result.stdout)
            
            if not current_version:
                self._logger.error("Could not parse CodeQL version from output")
                return CodeQLInstallationInfo(
                    is_installed=True,
                    version=None,
                    installation_path=installation_path,
                    is_latest_version=False,
                    available_latest_version=None
                )
            
            self._logger.info(f"Found CodeQL version: {current_version}")
            
            # Try to get latest version for comparison
            try:
                latest_version = await self.get_latest_version()
                is_latest = self._compare_versions(current_version, latest_version) >= 0
                
                self._logger.info(f"Latest CodeQL version: {latest_version}")
                self._logger.info(f"Installation is up to date: {is_latest}")
                
                return CodeQLInstallationInfo(
                    is_installed=True,
                    version=current_version,
                    installation_path=installation_path,
                    is_latest_version=is_latest,
                    available_latest_version=latest_version
                )
                
            except Exception as e:
                self._logger.warning(f"Could not check latest version: {e}")
                # Return info without latest version comparison
                return CodeQLInstallationInfo(
                    is_installed=True,
                    version=current_version,
                    installation_path=installation_path,
                    is_latest_version=True,  # Assume latest if we can't check
                    available_latest_version=None
                )
                
        except Exception as e:
            self._logger.error(f"Error validating CodeQL installation: {e}")
            return CodeQLInstallationInfo(
                is_installed=False,
                version=None,
                installation_path=None,
                is_latest_version=False,
                available_latest_version=None
            )

    async def get_latest_version(self) -> str:
        """
        Get the latest version of CodeQL bundle from GitHub CodeQL Action releases.
        
        Returns:
            CodeQL version string (e.g. "2.10.0")
        
        Raises:
            CodeQLError: If unable to fetch version information
        """
        self._logger.info("Fetching latest CodeQL version from GitHub")
        
        try:
            # Prepare headers for GitHub API request
            headers = self._get_github_headers()
            
            # Use the CodeQL Action repository to get the latest bundle version
            url = CodeQLConstants.GITHUB_RELEASES_LATEST_URL
            
            async with aiohttp.ClientSession() as session:
                timeout = aiohttp.ClientTimeout(total=10)
                async with session.get(url, headers=headers, timeout=timeout) as response:
                    if response.status == 403:
                        self._logger.error("GitHub API rate limit exceeded")
                        raise CodeQLError("GitHub API rate limit exceeded - consider using GITHUB_TOKEN")
                    
                    if response.status != 200:
                        error_msg = f"GitHub API request failed with status {response.status}"
                        self._logger.error(error_msg)
                        raise CodeQLError(error_msg)
                    
                    data = await response.json()
                    tag_name = data.get("tag_name")
                    
                    if not tag_name or not isinstance(tag_name, str):
                        raise CodeQLError("Invalid or missing tag_name in GitHub API response")
                    
                    # Extract version number from tag (e.g., "v2.22.2" -> "2.22.2")
                    version = self._extract_version_from_tag(tag_name)
                    
                    self._logger.info(f"Latest CodeQL version: {version}")
                    return version
                    
        except aiohttp.ClientError as e:
            error_msg = f"Network error fetching latest CodeQL version: {e}"
            self._logger.error(error_msg)
            raise CodeQLError(error_msg)
            
        except Exception as e:
            error_msg = f"Failed to fetch latest CodeQL version: {e}"
            self._logger.error(error_msg)
            raise CodeQLError(error_msg)
    
    async def install(
        self, 
        version: str = "", 
        force_reinstall: bool = False,
        persistent_path: bool = True
    ) -> CodeQLInstallationInfo:
        """
        Install or upgrade CodeQL bundle to a specific version.
        
        Args:
            version: The version of CodeQL bundle to install (empty string for latest)
            force_reinstall: Whether to reinstall even if version exists
            persistent_path: Whether to make PATH changes persistent across sessions
            
        Returns:
            Installation information after installation attempt
            
        Raises:
            CodeQLInstallationError: If installation fails
        """
        target_version = ""
        try:
            # Determine target version
            if not version:
                self._logger.info("No version specified, fetching latest version")
                target_version = await self.get_latest_version()
            else:
                target_version = version
                
            self._logger.info(f"Installing CodeQL bundle version {target_version}")
            
            # Check current installation unless force reinstall
            if not force_reinstall:
                current_info = await self.validate_installation()
                if (current_info.is_installed and 
                    current_info.version == target_version):
                    self._logger.info(f"CodeQL {target_version} already installed")
                    return current_info
            
            # Create installation directory
            install_dir = Path(self._installation_directory)
            try:
                self._os_operations.create_directory(install_dir)
            except FileSystemError as e:
                raise CodeQLInstallationError(f"Failed to create installation directory: {e}", installation_path=str(install_dir))
            
            # Download and install
            await self._download_and_install_bundle(target_version, install_dir)
            
            # Add to system PATH
            self._add_to_system_path(install_dir, persistent=persistent_path)
            
            # Verify installation by checking the installed executable directly
            verification_info = await self._verify_installation_at_path(install_dir, target_version)
            
            if verification_info.is_installed:
                self._logger.info(f"Successfully installed CodeQL {target_version}")
                return verification_info
            else:
                raise CodeQLInstallationError(
                    f"Installation verification failed for version {target_version}",
                    installation_path=str(install_dir)
                )
                
        except Exception as e:
            error_msg = f"Failed to install CodeQL version {target_version}: {e}"
            self._logger.error(error_msg)
            raise CodeQLInstallationError(
                error_msg, 
                installation_path=self._installation_directory
            )
    
    async def execute_command(
        self,
        command_args: List[str],
        working_directory: Optional[str] = None,
        timeout_seconds: Optional[int] = None
    ) -> CodeQLExecutionResult:
        """
        Execute arbitrary CodeQL CLI command with arguments.
        
        Args:
            command_args: List of command arguments (excluding 'codeql')
            working_directory: Directory to execute command in
            timeout_seconds: Maximum execution time
            
        Returns:
            Raw execution result
            
        Raises:
            CodeQLExecutionError: If command execution fails
        """
        self._logger.info(f"Executing CodeQL command: {' '.join(command_args)}")
        
        try:
            # Set up CodeQL CLI wrapper if needed
            self._setup_codeql_cli()
            
            # Execute command using the CLI wrapper
            # Note: _setup_codeql_cli ensures _codeql_cli is not None
            assert self._codeql_cli is not None, "CodeQL CLI should be initialized after setup"
            result = await self._codeql_cli.execute_command(
                command_args=command_args,
                working_directory=working_directory,
                timeout_seconds=timeout_seconds
            )
            
            # Log execution details
            if result.success:
                self._logger.debug(f"CodeQL command completed successfully in {result.execution_time_seconds:.2f}s")
            else:
                self._logger.warning(f"CodeQL command failed with exit code {result.exit_code}")
                if result.stderr:
                    self._logger.warning(f"Error output: {result.stderr}")
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to execute CodeQL command: {e}"
            self._logger.error(error_msg)
            raise CodeQLExecutionError(
                message=error_msg,
                command=" ".join(["codeql"] + command_args),
                stderr=str(e)
            )

    # Private helper methods for implementation details
    
    def _get_github_headers(self) -> Dict[str, str]:
        """Get headers for GitHub API requests."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        
        # Use GitHub token if available (from initialization or environment)
        github_token = self._github_token or self._os_operations.get_environment_variable("GITHUB_TOKEN")
        if github_token:
            headers["Authorization"] = f"Bearer {github_token}"
            self._logger.debug("Using GitHub token for API authentication")
        else:
            self._logger.warning("No GitHub token found - using unauthenticated requests")
        
        return headers
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """
        Compare two version strings.
        
        Returns:
            -1 if version1 < version2
             0 if version1 == version2
             1 if version1 > version2
        """
        def parse_version(version: str) -> tuple:
            """Parse version string into comparable tuple."""
            # Remove 'v' prefix if present and clean up
            clean_version = version.lstrip('v').strip()
            
            # Split by dots and convert to integers
            parts = []
            for part in clean_version.split('.'):
                # Handle pre-release versions (e.g., "2.10.0-rc1")
                if '-' in part:
                    part = part.split('-')[0]
                
                try:
                    parts.append(int(part))
                except ValueError:
                    parts.append(0)
            
            # Ensure we have at least 3 parts (major.minor.patch)
            while len(parts) < 3:
                parts.append(0)
                
            return tuple(parts)
        
        try:
            v1_tuple = parse_version(version1)
            v2_tuple = parse_version(version2)
            
            if v1_tuple < v2_tuple:
                return -1
            elif v1_tuple > v2_tuple:
                return 1
            else:
                return 0
                
        except Exception as e:
            self._logger.warning(f"Error comparing versions {version1} and {version2}: {e}")
            return 0  # Assume equal if we can't compare
    
    def _parse_version_string(self, version_output: str) -> str:
        """Parse version string from CodeQL CLI output."""
        # Common patterns for CodeQL version output
        patterns = [
            r'CodeQL command-line toolchain release (\d+\.\d+\.\d+)',
            r'version (\d+\.\d+\.\d+)',
            r'(\d+\.\d+\.\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, version_output)
            if match:
                return match.group(1)
        
        # If no pattern matches, try to extract any version-like string
        version_match = re.search(r'(\d+\.\d+\.\d+)', version_output)
        if version_match:
            return version_match.group(1)
            
        self._logger.warning(f"Could not parse version from output: {version_output}")
        return ""
    
    def _parse_installation_path(self, version_output: str) -> str:
        """Parse installation path from CodeQL CLI --version output."""
        # Look for "Unpacked in:" line in the version output
        patterns = [
            r'Unpacked in:\s*(.+)',
            r'Installed in:\s*(.+)',
            r'Location:\s*(.+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, version_output, re.MULTILINE)
            if match:
                path = match.group(1).strip()
                self._logger.debug(f"Found installation path: {path}")
                return path
        
        # If no installation path found, log the output for debugging
        self._logger.debug(f"Could not parse installation path from output: {version_output}")
        return "unknown"
    
    def _extract_version_from_tag(self, tag_name: str) -> str:
        """Extract version number from GitHub release tag."""
        # Remove common prefixes from tag names
        # e.g., "v2.22.2" -> "2.22.2", "codeql-bundle-v2.22.1" -> "2.22.1"
        patterns = [
            r'codeql-bundle-v(\d+\.\d+\.\d+)',  # codeql-bundle-v2.22.1
            r'v(\d+\.\d+\.\d+)',                # v2.22.2
            r'(\d+\.\d+\.\d+)',                 # 2.22.2
        ]
        
        for pattern in patterns:
            match = re.search(pattern, tag_name)
            if match:
                version = match.group(1)
                self._logger.debug(f"Extracted version '{version}' from tag '{tag_name}'")
                return version
        
        # If no pattern matches, return the tag as-is but log a warning
        self._logger.warning(f"Could not extract version from tag: {tag_name}")
        return tag_name
    
    def _setup_codeql_cli(self) -> None:
        """Initialize CodeQL CLI wrapper if not already done."""
        if self._codeql_cli is not None:
            return
            
        try:
            # Try to create CodeQL CLI wrapper
            # If custom executable path is provided, use it
            if self._executable_path:
                self._codeql_cli = CodeQLCLI(self._executable_path)
            else:
                # Let CodeQLCLI find the executable (it will search PATH)
                self._codeql_cli = CodeQLCLI()
                
            self._logger.debug("CodeQL CLI wrapper initialized successfully")
            
        except Exception as e:
            error_msg = f"Failed to initialize CodeQL CLI: {e}"
            self._logger.error(error_msg)
            raise CodeQLNotInstalledError(error_msg)
    
    async def _download_and_install_bundle(self, version: str, install_dir: Path) -> None:
        """Download and install CodeQL bundle for specified version."""
        self._logger.info(f"Downloading CodeQL bundle version {version}")
        
        try:
            # Get download URL for the bundle
            download_url = await self._get_bundle_download_url(version)
            
            # Determine file extension from URL
            if download_url.endswith('.zip'):
                suffix = '.zip'
            elif download_url.endswith('.tar.gz'):
                suffix = '.tar.gz'
            else:
                suffix = '.zip'  # Default fallback
                
            # Create temporary file for download
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
                temp_path = temp_file.name
                
            try:
                # Download the bundle
                await self._download_file(download_url, temp_path)
                
                # Remove existing installation if present
                codeql_dir = install_dir / "codeql"
                if codeql_dir.exists():
                    self._logger.info(f"Removing existing installation at {codeql_dir}")
                    try:
                        self._os_operations.remove_directory(codeql_dir)
                    except FileSystemError as e:
                        self._logger.warning(f"Failed to remove existing installation: {e}")
                        # Continue with installation anyway
                
                # Extract the bundle
                await self._extract_bundle(temp_path, install_dir, download_url)
                
                # Set executable permissions
                self._set_executable_permissions(install_dir)
                
                self._logger.info(f"Successfully installed CodeQL bundle {version}")
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            error_msg = f"Failed to download and install bundle: {e}"
            self._logger.error(error_msg)
            raise CodeQLInstallationError(error_msg, installation_path=str(install_dir))
    
    async def _get_bundle_download_url(self, version: str) -> str:
        """Get download URL for CodeQL bundle."""
        try:
            headers = self._get_github_headers()
            
            # Get release info for the version
            if version == await self.get_latest_version():
                # Use latest release endpoint
                url = CodeQLConstants.GITHUB_RELEASES_LATEST_URL
            else:
                # Use specific release endpoint
                tag = f"codeql-bundle-v{version}"
                url = f"{CodeQLConstants.GITHUB_RELEASES_TAG_URL}/{tag}"
            
            async with aiohttp.ClientSession() as session:
                timeout = aiohttp.ClientTimeout(total=10)
                async with session.get(url, headers=headers, timeout=timeout) as response:
                    if response.status != 200:
                        raise CodeQLError(f"Failed to get release info: HTTP {response.status}")
                    
                    data = await response.json()
                    assets = data.get("assets", [])
                    
                    # Find the appropriate bundle for current platform
                    platform_suffix = self._get_platform_bundle_suffix()
                    
                    for asset in assets:
                        asset_name = asset.get("name", "")
                        if asset_name.endswith(platform_suffix):
                            download_url = asset.get("browser_download_url")
                            if download_url:
                                self._logger.info(f"Found bundle: {asset_name}")
                                return download_url
                    
                    # If no platform-specific bundle found, list available assets
                    available_assets = [asset.get("name", "unknown") for asset in assets]
                    raise CodeQLError(
                        f"No suitable bundle found for platform. "
                        f"Looking for suffix '{platform_suffix}'. "
                        f"Available assets: {available_assets}"
                    )
                    
        except Exception as e:
            error_msg = f"Failed to get download URL for version {version}: {e}"
            self._logger.error(error_msg)
            raise CodeQLError(error_msg)
    
    def _get_platform_bundle_suffix(self) -> str:
        """Get the appropriate bundle suffix for current platform."""
        platform_info = self._platform_info
        system = platform_info["system"]
        
        if system == "windows":
            return "win64.zip"
        elif system == "darwin":
            return "osx64.tar.gz"
        elif system == "linux":
            return "linux64.tar.gz"
        else:
            # Default to linux64 for unknown platforms
            self._logger.warning(f"Unknown platform {system}, defaulting to linux64")
            return "linux64.tar.gz"
    
    async def _download_file(self, url: str, destination_path: str) -> None:
        """Download file from URL to destination."""
        self._logger.info(f"Downloading from {url}")
        
        try:
            headers = self._get_github_headers()
            
            async with aiohttp.ClientSession() as session:
                timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes for large files
                async with session.get(url, headers=headers, timeout=timeout) as response:
                    if response.status != 200:
                        raise CodeQLError(f"Download failed: HTTP {response.status}")
                    
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    
                    with open(destination_path, 'wb') as file:
                        async for chunk in response.content.iter_chunked(8192):
                            file.write(chunk)
                            downloaded += len(chunk)
                            
                            # Log progress for large files
                            if total_size > 0 and downloaded % (1024 * 1024) == 0:  # Every MB
                                progress = (downloaded / total_size) * 100
                                self._logger.debug(f"Download progress: {progress:.1f}%")
                    
                    self._logger.info(f"Downloaded {downloaded} bytes to {destination_path}")
                    
        except Exception as e:
            error_msg = f"Failed to download file: {e}"
            self._logger.error(error_msg)
            raise CodeQLError(error_msg)
    
    async def _extract_bundle(self, archive_path: str, extract_to: Path, download_url: str = "") -> None:
        """Extract CodeQL bundle archive."""
        self._logger.info(f"Extracting bundle to {extract_to}")
        
        try:
            # Determine file type from path or URL
            is_zip = archive_path.endswith('.zip') or download_url.endswith('.zip')
            is_targz = archive_path.endswith('.tar.gz') or download_url.endswith('.tar.gz')
            
            if is_zip:
                # Handle ZIP files (Windows)
                self._logger.debug("Extracting ZIP archive")
                with zipfile.ZipFile(archive_path, 'r') as zip_file:
                    zip_file.extractall(extract_to)
            elif is_targz:
                # Handle tar.gz files (Linux/macOS)
                self._logger.debug("Extracting TAR.GZ archive")
                with tarfile.open(archive_path, 'r:gz') as tar_file:
                    tar_file.extractall(extract_to)
            else:
                # Try to detect by reading file header
                self._logger.debug("Attempting to detect archive type by content")
                try:
                    with zipfile.ZipFile(archive_path, 'r') as zip_file:
                        zip_file.extractall(extract_to)
                        self._logger.debug("Successfully extracted as ZIP")
                except zipfile.BadZipFile:
                    try:
                        with tarfile.open(archive_path, 'r:gz') as tar_file:
                            tar_file.extractall(extract_to)
                            self._logger.debug("Successfully extracted as TAR.GZ")
                    except tarfile.TarError:
                        raise CodeQLError(f"Unable to determine archive format for: {archive_path}")
                
            self._logger.info("Bundle extraction completed")
            
        except Exception as e:
            error_msg = f"Failed to extract bundle: {e}"
            self._logger.error(error_msg)
            raise CodeQLError(error_msg)
    
    def _set_executable_permissions(self, install_dir: Path) -> None:
        """Set executable permissions on CodeQL binaries."""
        codeql_dir = install_dir / "codeql"
        
        if not codeql_dir.exists():
            raise CodeQLError(f"CodeQL directory not found after extraction: {codeql_dir}")
        
        # Find the main codeql executable
        executable_paths = []
        
        # Common locations for the executable
        potential_executables = [
            codeql_dir / "codeql",
            codeql_dir / "codeql.exe",
            codeql_dir / "bin" / "codeql",
            codeql_dir / "bin" / "codeql.exe"
        ]
        
        for exec_path in potential_executables:
            if exec_path.exists():
                executable_paths.append(exec_path)
        
        if not executable_paths:
            # Search recursively for codeql executable
            for file_path in codeql_dir.rglob("codeql*"):
                if file_path.is_file() and ("codeql" in file_path.name):
                    executable_paths.append(file_path)
        
        if not executable_paths:
            raise CodeQLError(f"CodeQL executable not found in {codeql_dir}")
        
        # Set executable permissions
        for exec_path in executable_paths:
            try:
                self._os_operations.set_executable_permissions(exec_path)
                self._logger.debug(f"Set executable permissions on {exec_path}")
            except PermissionError as e:
                self._logger.warning(f"Failed to set executable permissions on {exec_path}: {e}")
                # Continue with other files
        
        self._logger.info(f"Attempted to set executable permissions on {len(executable_paths)} files")
    
    async def _verify_installation_at_path(
        self, 
        install_dir: Path, 
        expected_version: str
    ) -> CodeQLInstallationInfo:
        """Verify CodeQL installation at a specific path."""
        try:
            codeql_executable = install_dir / "codeql" / "codeql"
            
            if not codeql_executable.exists() or not codeql_executable.is_file():
                self._logger.warning(f"CodeQL executable not found at {codeql_executable}")
                return CodeQLInstallationInfo(
                    is_installed=False,
                    version=None,
                    installation_path=None
                )
            
            # Check if executable has proper permissions
            if not self._os_operations.is_executable(codeql_executable):
                self._logger.warning(f"CodeQL executable at {codeql_executable} is not executable")
                return CodeQLInstallationInfo(
                    is_installed=False,
                    version=None,
                    installation_path=None
                )
            
            # Create a temporary CLI instance for this specific executable
            from ..external_tools.codeql_wrapper import CodeQLCLI
            temp_cli = CodeQLCLI(str(codeql_executable))
            
            # Get version from the installed executable
            result = await temp_cli.execute_command(
                ["version", "--format=json"],
                timeout_seconds=30
            )
            
            if result.exit_code != 0:
                self._logger.warning(f"Failed to get version from {codeql_executable}: {result.stderr}")
                return CodeQLInstallationInfo(
                    is_installed=False,
                    version=None,
                    installation_path=None
                )
            
            # Parse version output
            version_data = json.loads(result.stdout)
            installed_version = version_data.get("productVersion", "unknown")
            
            return CodeQLInstallationInfo(
                is_installed=True,
                version=installed_version,
                installation_path=str(codeql_executable)
            )
            
        except Exception as e:
            self._logger.error(f"Error verifying installation at {install_dir}: {e}")
            return CodeQLInstallationInfo(
                is_installed=False,
                version=None,
                installation_path=None
            )

    def _add_to_system_path(self, install_dir: Path, persistent: bool = True) -> None:
        """Add CodeQL installation to system PATH."""
        codeql_dir = install_dir / "codeql"
        
        if not codeql_dir.exists():
            self._logger.warning(f"CodeQL directory not found: {codeql_dir}")
            return
        
        platform_info = self._platform_info
        system = platform_info["system"]
        
        if system == "windows":
            codeql_executable = codeql_dir / "bin" / "codeql"
        elif system == "darwin":
            codeql_executable = codeql_dir / "codeql"
        elif system == "linux":
            codeql_executable = codeql_dir / "codeql"
        else:
            # Default to linux64 for unknown platforms
            self._logger.warning(f"Unknown platform {system}, defaulting to linux64")
            codeql_executable = codeql_dir / "codeql"

        # Add to PATH for current session
        self._os_operations.set_environment_variable("CODEQL_PATH", str(codeql_executable))
        
        # Add the directory containing the executable to PATH
        codeql_bin_dir = str(codeql_executable.parent)
        self._os_operations.add_to_current_path(codeql_bin_dir)
        self._logger.info(f"Added {codeql_bin_dir} to current session PATH")

        # Make changes persistent if requested
        if persistent:
            try:
                self._make_path_persistent(codeql_bin_dir, system)
            except Exception as e:
                self._logger.warning(f"Failed to make PATH changes persistent: {e}")
                self._logger.info(
                    f"To manually add to PATH, add this to your shell profile:\n"
                    f"export PATH=\"{codeql_bin_dir}:$PATH\""
                )

    def _make_path_persistent(self, codeql_bin_dir: str, system: str) -> None:
        """Make CodeQL PATH changes persistent across sessions."""
        try:
            if system == "windows":
                was_added = self._os_operations.make_path_persistent_windows(codeql_bin_dir)
                if was_added:
                    self._logger.info(f"Added {codeql_bin_dir} to Windows user PATH")
                    self._logger.info("Note: You may need to restart terminal/IDE for changes to take effect")
                else:
                    self._logger.info(f"CodeQL directory already in Windows PATH")
            else:
                was_added, target_profile = self._os_operations.make_path_persistent_unix(codeql_bin_dir)
                if was_added:
                    self._logger.info(f"Added CodeQL to PATH in {target_profile}")
                    self._logger.info("Note: Restart your shell or run 'source ~/.profile' for changes to take effect")
                else:
                    self._logger.info(f"CodeQL directory already in {target_profile}")
        except (EnvironmentError, FileSystemError) as e:
            self._logger.warning(f"Failed to make PATH persistent: {e}")
            self._logger.info(
                f"To manually add to PATH, add this to your shell profile:\n"
                f"export PATH=\"{codeql_bin_dir}:$PATH\""
            )

# Factory function for creating CodeQL service instance
def create_codeql_service(
    installation_directory: Optional[str] = None,
    github_token: Optional[str] = None,
    executable_path: Optional[str] = None,
) -> CodeQLService:
    """
    Factory function to create CodeQL service implementation.
    
    Args:
        installation_directory: Custom directory for CodeQL installation
        github_token: GitHub token for API access
        executable_path: Custom path to existing CodeQL executable
        
    Returns:
        Configured CodeQL service implementation
    """
    return CodeQLServiceImpl(
        installation_directory=installation_directory,
        github_token=github_token,
        executable_path=executable_path,
    )