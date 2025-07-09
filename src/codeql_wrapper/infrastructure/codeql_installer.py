"""CodeQL installer infrastructure module."""

import json
import os
import platform
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.request import urlretrieve, urlopen

from .logger import get_logger


class CodeQLInstaller:
    """Handles downloading and installing CodeQL CLI."""

    def __init__(self, install_dir: Optional[str] = None):
        """
        Initialize CodeQL installer.

        Args:
            install_dir: Directory to install CodeQL. Defaults to ~/.codeql

        Raises:
            ValueError: If install_dir is provided but invalid
        """
        self.logger = get_logger(__name__)

        # Validate and set install directory
        if install_dir:
            install_path = Path(install_dir)
            if install_path.exists() and install_path.is_file():
                raise ValueError(f"Install directory cannot be a file: {install_dir}")
            self.install_dir = install_path
        else:
            self.install_dir = Path.home() / ".codeql"

        # Set binary name based on platform
        binary_name = (
            "codeql.exe" if platform.system().lower() == "windows" else "codeql"
        )
        self.codeql_binary = self.install_dir / "codeql" / binary_name

    def get_latest_version(self) -> str:
        """
        Get the latest CodeQL version from GitHub releases.

        Returns:
            Latest version string (e.g., 'codeql-bundle-v2.22.1')

        Raises:
            Exception: If unable to fetch the latest version from GitHub API
        """
        api_url = "https://api.github.com/repos/github/codeql-action/releases/latest"

        self.logger.info("Fetching latest CodeQL version from GitHub API")
        try:
            with urlopen(api_url) as response:
                if response.status != 200:
                    raise Exception(f"GitHub API returned status {response.status}")

                data: Dict[str, Any] = json.loads(response.read().decode("utf-8"))
                latest_version = data.get("tag_name")

                if not latest_version or not isinstance(latest_version, str):
                    raise Exception("No valid tag_name found in GitHub API response")

                # The GitHub API returns tags like "codeql-bundle-v2.22.1"
                # from codeql-action
                # This is already the correct format for bundle releases
                self.logger.info(f"Latest CodeQL version: {latest_version}")
                return str(latest_version)  # Explicit cast to satisfy mypy
        except Exception as e:
            self.logger.error(f"Failed to fetch latest CodeQL version: {e}")
            raise Exception(f"Unable to fetch latest CodeQL version: {e}") from e

    def get_platform_bundle_name(self) -> str:
        """
        Get the platform-specific bundle name for CodeQL.

        Returns:
            Platform-specific bundle name (e.g., 'linux64', 'osx64', 'win64')
        """
        system = platform.system().lower()
        machine = platform.machine().lower()

        if system == "linux":
            return "linux64"
        elif system == "darwin":  # macOS
            return "osx64"
        elif system == "windows":
            return "win64"
        else:
            # Default to linux64 for unknown platforms
            self.logger.warning(
                f"Unknown platform: {system} {machine}, defaulting to linux64"
            )
            return "linux64"

    def get_download_url(self, version: Optional[str] = None) -> str:
        """
        Get the download URL for CodeQL bundle.

        Args:
            version: CodeQL version to download. If None, uses the latest version.
                   Can be in format 'v2.22.1' or 'codeql-bundle-v2.22.1'

        Returns:
            Download URL for the CodeQL bundle
        """
        if version is None or version == "latest":
            version = self.get_latest_version()

        # Normalize version format for URL construction
        # If version doesn't start with 'codeql-bundle-', add it
        if not version.startswith("codeql-bundle-"):
            # Handle cases like 'v2.22.1' -> 'codeql-bundle-v2.22.1'
            if not version.startswith("v"):
                version = f"v{version}"
            version = f"codeql-bundle-{version}"

        # Use codeql-action repository for downloading bundles
        base_url = "https://github.com/github/codeql-action/releases/download"
        platform = self.get_platform_bundle_name()
        return f"{base_url}/{version}/codeql-bundle-{platform}.tar.gz"

    def is_installed(self) -> bool:
        """
        Check if CodeQL is already installed.

        Returns:
            True if CodeQL binary exists and is executable
        """
        if not self.codeql_binary.exists():
            return False

        # On Windows, just check if file exists since .exe files
        # are executable by default
        if platform.system().lower() == "windows":
            return True

        # On Unix-like systems, check executable permission
        return os.access(self.codeql_binary, os.X_OK)

    def get_version(self) -> Optional[str]:
        """
        Get the installed CodeQL version.

        Returns:
            Version string if CodeQL is installed, None otherwise
        """
        if not self.is_installed():
            return None

        try:
            result = subprocess.run(
                [str(self.codeql_binary), "version", "--format=json"],
                capture_output=True,
                text=True,
                check=True,
            )
            version_info = json.loads(result.stdout)
            version = version_info.get("version")
            return version if version is not None else "unknown"
        except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
            return None

    def download_codeql(self, version: Optional[str] = None) -> Path:
        """
        Download CodeQL bundle.

        Args:
            version: CodeQL version to download. If None, uses the latest version.

        Returns:
            Path to downloaded tar.gz file

        Raises:
            Exception: If download fails
        """
        if version is None:
            version = self.get_latest_version()

        download_url = self.get_download_url(version)
        self.logger.info(f"Downloading CodeQL {version} from {download_url}")

        # Create temporary file for download
        temp_dir = Path(tempfile.mkdtemp())
        download_path = temp_dir / f"codeql-bundle-{version}.tar.gz"

        try:
            urlretrieve(download_url, download_path)
            self.logger.info(f"Downloaded CodeQL bundle to {download_path}")
            return download_path
        except Exception as e:
            self.logger.error(f"Failed to download CodeQL: {e}")
            # Clean up temp directory on failure
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise Exception(f"Failed to download CodeQL from {download_url}: {e}")

    def extract_codeql(self, tar_path: Path) -> None:
        """
        Extract CodeQL bundle to installation directory.

        Args:
            tar_path: Path to the downloaded tar.gz file

        Raises:
            Exception: If extraction fails
        """
        self.logger.info(f"Extracting CodeQL to {self.install_dir}")

        try:
            # Create installation directory
            self.install_dir.mkdir(parents=True, exist_ok=True)

            # Extract tar.gz file
            with tarfile.open(tar_path, "r:gz") as tar:
                # Use data filter for security if available (Python 3.12+)
                try:
                    tar.extractall(path=self.install_dir, filter="data")
                except TypeError:
                    # Fallback for older Python versions - use safe extraction
                    self._safe_extract(tar, self.install_dir)

            # Make codeql binary executable (Unix/Linux/macOS only)
            if self.codeql_binary.exists():
                if platform.system().lower() != "windows":
                    os.chmod(self.codeql_binary, 0o755)
                self.logger.info(f"CodeQL extracted successfully to {self.install_dir}")
            else:
                raise Exception("CodeQL binary not found after extraction")

        except Exception as e:
            self.logger.error(f"Failed to extract CodeQL: {e}")
            raise Exception(f"Failed to extract CodeQL: {e}")

    def install(self, version: Optional[str] = None, force: bool = False) -> str:
        """
        Download and install CodeQL.

        Args:
            version: CodeQL version to install. If None, uses the latest version.
            force: Force reinstallation even if already installed

        Returns:
            Path to the installed CodeQL binary

        Raises:
            Exception: If installation fails
        """
        if version is None:
            version = self.get_latest_version()

        # Check if already installed
        if self.is_installed() and not force:
            installed_version = self.get_version()
            self.logger.info(
                f"CodeQL is already installed (version: {installed_version})"
            )
            return str(self.codeql_binary)

        self.logger.info(f"Installing CodeQL {version}")

        try:
            # Download CodeQL bundle
            tar_path = self.download_codeql(version)

            try:
                # Remove existing installation if force is True
                if force and self.install_dir.exists():
                    self.logger.info("Removing existing CodeQL installation")
                    shutil.rmtree(self.install_dir)

                # Extract CodeQL
                self.extract_codeql(tar_path)

                # Verify installation
                if not self.is_installed():
                    raise Exception("CodeQL installation verification failed")

                installed_version = self.get_version()
                self.logger.info(
                    f"CodeQL {installed_version} installed successfully at "
                    f"{self.codeql_binary}"
                )

                return str(self.codeql_binary)

            finally:
                # Clean up downloaded file
                if tar_path.exists():
                    shutil.rmtree(tar_path.parent, ignore_errors=True)

        except Exception as e:
            self.logger.error(f"CodeQL installation failed: {e}")
            raise

    def get_binary_path(self) -> Optional[str]:
        """
        Get the path to the CodeQL binary.

        Returns:
            Path to CodeQL binary if installed, None otherwise
        """
        if self.is_installed():
            return str(self.codeql_binary)
        return None

    # Private methods
    def _safe_extract(self, tar: tarfile.TarFile, extract_path: Path) -> None:
        """
        Safely extract tar file members, preventing path traversal attacks.

        Args:
            tar: The tarfile object to extract from
            extract_path: The base path to extract to

        Raises:
            Exception: If a member has an unsafe path
        """
        for member in tar.getmembers():
            # Resolve the full path where the member would be extracted
            member_path = extract_path / member.name

            # Normalize and resolve the path to handle any '..' components
            try:
                resolved_path = member_path.resolve()
                extract_path_resolved = extract_path.resolve()
            except OSError:
                # If we can't resolve the path, it's potentially dangerous
                raise Exception(f"Unsafe path in archive: {member.name}")

            # Check if the resolved path is within the extraction directory
            try:
                resolved_path.relative_to(extract_path_resolved)
            except ValueError:
                # The path escapes the extraction directory
                raise Exception(f"Path traversal attempt detected: {member.name}")

            # Additional checks for suspicious characters and patterns
            if ".." in member.name or member.name.startswith("/"):
                raise Exception(f"Unsafe path in archive: {member.name}")

            # Extract this member safely
            tar.extract(member, path=extract_path)
