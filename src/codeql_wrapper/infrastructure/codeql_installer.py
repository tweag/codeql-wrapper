"""CodeQL installer infrastructure module."""

import json
import os
import platform
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path
from typing import Optional
from urllib.request import urlretrieve

from .logger import get_logger


class CodeQLInstaller:
    """Handles downloading and installing CodeQL CLI."""

    def __init__(self, install_dir: Optional[str] = None):
        """
        Initialize CodeQL installer.

        Args:
            install_dir: Directory to install CodeQL. Defaults to ~/.codeql
        """
        self.logger = get_logger(__name__)
        self.install_dir = Path(install_dir or Path.home() / ".codeql")

        # Set binary name based on platform
        binary_name = (
            "codeql.exe" if platform.system().lower() == "windows" else "codeql"
        )
        self.codeql_binary = self.install_dir / "codeql" / binary_name

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

    def get_download_url(self, version: str = "v2.22.1") -> str:
        """
        Get the download URL for CodeQL bundle.

        Args:
            version: CodeQL version to download (e.g., 'v2.22.1')

        Returns:
            Download URL for the CodeQL bundle
        """
        base_url = "https://github.com/github/codeql-action/releases/download"
        platform_bundle = self.get_platform_bundle_name()
        return (
            f"{base_url}/codeql-bundle-{version}/codeql-bundle-{platform_bundle}.tar.gz"
        )

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

    def download_codeql(self, version: str = "v2.22.1") -> Path:
        """
        Download CodeQL bundle.

        Args:
            version: CodeQL version to download

        Returns:
            Path to downloaded tar.gz file

        Raises:
            Exception: If download fails
        """
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

    def install(self, version: str = "v2.22.1", force: bool = False) -> str:
        """
        Download and install CodeQL.

        Args:
            version: CodeQL version to install
            force: Force reinstallation even if already installed

        Returns:
            Path to the installed CodeQL binary

        Raises:
            Exception: If installation fails
        """
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

    def uninstall(self) -> None:
        """
        Uninstall CodeQL by removing the installation directory.

        Raises:
            Exception: If uninstallation fails
        """
        if not self.install_dir.exists():
            self.logger.info("CodeQL is not installed")
            return

        try:
            self.logger.info(f"Uninstalling CodeQL from {self.install_dir}")
            shutil.rmtree(self.install_dir)
            self.logger.info("CodeQL uninstalled successfully")
        except Exception as e:
            self.logger.error(f"Failed to uninstall CodeQL: {e}")
            raise Exception(f"Failed to uninstall CodeQL: {e}")

    def get_binary_path(self) -> Optional[str]:
        """
        Get the path to the CodeQL binary.

        Returns:
            Path to CodeQL binary if installed, None otherwise
        """
        if self.is_installed():
            return str(self.codeql_binary)
        return None
