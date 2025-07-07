"""Tests for the CodeQL installer infrastructure module."""

import json
import os
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from codeql_wrapper.infrastructure.codeql_installer import CodeQLInstaller


class TestCodeQLInstaller:
    """Test cases for the CodeQL installer."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        # Create a temporary directory for testing
        self.temp_dir = Path(tempfile.mkdtemp())
        self.installer = CodeQLInstaller(install_dir=str(self.temp_dir))

    def teardown_method(self) -> None:
        """Clean up test fixtures."""
        # Clean up temporary directory
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_download_url(self) -> None:
        """Test download URL generation."""
        url = self.installer.get_download_url("v2.22.1")
        # Test should work on both macOS (osx64) and Linux (linux64)
        assert "codeql-bundle-v2.22.1" in url
        assert url.endswith(".tar.gz")
        assert "github.com/github/codeql-action/releases/download" in url

    def test_is_installed_false_when_not_exists(self) -> None:
        """Test is_installed returns False when binary doesn't exist."""
        assert not self.installer.is_installed()

    def test_is_installed_true_when_exists_and_executable(self) -> None:
        """Test is_installed returns True when binary exists and is executable."""
        # Create the codeql directory and binary
        codeql_dir = self.temp_dir / "codeql"
        codeql_dir.mkdir(parents=True)
        binary_path = codeql_dir / "codeql"
        binary_path.touch()
        os.chmod(binary_path, 0o755)

        assert self.installer.is_installed()

    def test_get_version_none_when_not_installed(self) -> None:
        """Test get_version returns None when CodeQL is not installed."""
        assert self.installer.get_version() is None

    @patch("subprocess.run")
    def test_get_version_success(self, mock_run) -> None:
        """Test get_version returns version when CodeQL is installed."""
        # Setup binary
        codeql_dir = self.temp_dir / "codeql"
        codeql_dir.mkdir(parents=True)
        binary_path = codeql_dir / "codeql"
        binary_path.touch()
        os.chmod(binary_path, 0o755)

        # Mock subprocess result
        mock_result = Mock()
        mock_result.stdout = json.dumps({"version": "2.22.1"})
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        version = self.installer.get_version()
        assert version == "2.22.1"

    @patch("subprocess.run")
    def test_get_version_handles_error(self, mock_run) -> None:
        """Test get_version handles subprocess errors."""
        # Setup binary
        codeql_dir = self.temp_dir / "codeql"
        codeql_dir.mkdir(parents=True)
        binary_path = codeql_dir / "codeql"
        binary_path.touch()
        os.chmod(binary_path, 0o755)

        # Mock subprocess to raise exception
        mock_run.side_effect = subprocess.CalledProcessError(1, "codeql")

        version = self.installer.get_version()
        assert version is None

    @patch("codeql_wrapper.infrastructure.codeql_installer.urlretrieve")
    def test_download_codeql_success(self, mock_urlretrieve) -> None:
        """Test successful CodeQL download."""
        version = "v2.22.1"

        # Mock successful download
        def mock_download(url, path):
            Path(path).touch()

        mock_urlretrieve.side_effect = mock_download

        result_path = self.installer.download_codeql(version)

        assert result_path.exists()
        assert f"codeql-bundle-{version}.tar.gz" in str(result_path)

        # Verify the URL was called (platform-agnostic check)
        mock_urlretrieve.assert_called_once()
        call_args = mock_urlretrieve.call_args[0]
        assert f"codeql-bundle-{version}" in call_args[0]
        assert (
            "https://github.com/github/codeql-action/releases/download" in call_args[0]
        )
        assert call_args[1] == result_path

    @patch("codeql_wrapper.infrastructure.codeql_installer.urlretrieve")
    def test_download_codeql_failure(self, mock_urlretrieve) -> None:
        """Test CodeQL download failure."""
        mock_urlretrieve.side_effect = Exception("Download failed")

        with pytest.raises(Exception, match="Failed to download CodeQL"):
            self.installer.download_codeql("v2.22.1")

    def test_get_binary_path_none_when_not_installed(self) -> None:
        """Test get_binary_path returns None when not installed."""
        assert self.installer.get_binary_path() is None

    def test_get_binary_path_returns_path_when_installed(self) -> None:
        """Test get_binary_path returns path when installed."""
        # Setup binary
        codeql_dir = self.temp_dir / "codeql"
        codeql_dir.mkdir(parents=True)
        binary_path = codeql_dir / "codeql"
        binary_path.touch()
        os.chmod(binary_path, 0o755)

        result = self.installer.get_binary_path()
        assert result == str(binary_path)

    @patch.object(CodeQLInstaller, "download_codeql")
    @patch.object(CodeQLInstaller, "extract_codeql")
    @patch.object(CodeQLInstaller, "is_installed")
    @patch.object(CodeQLInstaller, "get_version")
    def test_install_success(
        self, mock_get_version, mock_is_installed, mock_extract, mock_download
    ) -> None:
        """Test successful CodeQL installation."""
        # Mock download to return a fake tar path
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            fake_tar = Path(tmp_file.name)
        mock_download.return_value = fake_tar

        # Mock installation check
        mock_is_installed.side_effect = [False, True]  # Not installed, then installed
        mock_get_version.return_value = "2.22.1"

        try:
            result = self.installer.install("v2.22.1")

            assert result == str(self.installer.codeql_binary)
            mock_download.assert_called_once_with("v2.22.1")
            mock_extract.assert_called_once_with(fake_tar)
        finally:
            # Clean up
            if fake_tar.exists():
                fake_tar.unlink()

    @patch.object(CodeQLInstaller, "is_installed")
    @patch.object(CodeQLInstaller, "get_version")
    def test_install_already_installed(
        self, mock_get_version, mock_is_installed
    ) -> None:
        """Test install when CodeQL is already installed."""
        mock_is_installed.return_value = True
        mock_get_version.return_value = "2.22.1"

        result = self.installer.install("v2.22.1")

        assert result == str(self.installer.codeql_binary)

    def test_uninstall_not_installed(self) -> None:
        """Test uninstall when CodeQL is not installed."""
        # Ensure the directory doesn't exist
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

        # Should not raise an exception
        self.installer.uninstall()

    def test_uninstall_success(self) -> None:
        """Test successful uninstall."""
        # Create installation directory
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        test_file = self.temp_dir / "test.txt"
        test_file.touch()

        self.installer.uninstall()

        assert not self.temp_dir.exists()

    def test_installer_initialization_default_dir(self) -> None:
        """Test installer initialization with default directory."""
        default_installer = CodeQLInstaller()
        expected_path = Path.home() / ".codeql"
        assert default_installer.install_dir == expected_path
        assert default_installer.codeql_binary == expected_path / "codeql" / "codeql"

    def test_installer_initialization_custom_dir(self) -> None:
        """Test installer initialization with custom directory."""
        custom_dir = "/custom/path"
        custom_installer = CodeQLInstaller(custom_dir)
        expected_path = Path(custom_dir)
        assert custom_installer.install_dir == expected_path
        assert custom_installer.codeql_binary == expected_path / "codeql" / "codeql"

    def test_get_download_url_different_versions(self) -> None:
        """Test download URL generation for different versions."""
        test_cases = ["v2.14.6", "v2.16.0", "latest"]

        for version in test_cases:
            url = self.installer.get_download_url(version)
            # Test should work on both macOS and Linux
            assert f"codeql-bundle-{version}" in url
            assert url.endswith(".tar.gz")
            assert "github.com/github/codeql-action/releases/download" in url

    def test_is_installed_false_when_not_executable(self) -> None:
        """Test is_installed returns False when binary exists but is not executable."""
        # Create the codeql directory and binary
        codeql_dir = self.temp_dir / "codeql"
        codeql_dir.mkdir(parents=True)
        binary_path = codeql_dir / "codeql"
        binary_path.touch()
        # Don't make it executable
        os.chmod(binary_path, 0o644)

        assert not self.installer.is_installed()

    @patch("subprocess.run")
    def test_get_version_handles_json_decode_error(self, mock_run) -> None:
        """Test get_version handles JSON decode errors."""
        # Setup binary
        codeql_dir = self.temp_dir / "codeql"
        codeql_dir.mkdir(parents=True)
        binary_path = codeql_dir / "codeql"
        binary_path.touch()
        os.chmod(binary_path, 0o755)

        # Mock subprocess to return invalid JSON
        mock_result = Mock()
        mock_result.stdout = "invalid json"
        mock_run.return_value = mock_result

        version = self.installer.get_version()
        assert version is None

    @patch("subprocess.run")
    def test_get_version_handles_missing_product_version(self, mock_run) -> None:
        """Test get_version handles missing productVersion in JSON."""
        # Setup binary
        codeql_dir = self.temp_dir / "codeql"
        codeql_dir.mkdir(parents=True)
        binary_path = codeql_dir / "codeql"
        binary_path.touch()
        os.chmod(binary_path, 0o755)

        # Mock subprocess to return JSON without productVersion
        mock_result = Mock()
        mock_result.stdout = json.dumps({"otherField": "value"})
        mock_run.return_value = mock_result

        version = self.installer.get_version()
        assert version == "unknown"

    @patch("codeql_wrapper.infrastructure.codeql_installer.urlretrieve")
    def test_download_codeql_cleans_up_on_failure(self, mock_urlretrieve) -> None:
        """Test that download_codeql cleans up temp directory on failure."""
        mock_urlretrieve.side_effect = Exception("Network error")

        # Capture the temp directory that gets created
        original_mkdtemp = tempfile.mkdtemp
        temp_dirs = []

        def capture_mkdtemp():
            temp_dir = original_mkdtemp()
            temp_dirs.append(temp_dir)
            return temp_dir

        with patch("tempfile.mkdtemp", side_effect=capture_mkdtemp):
            with pytest.raises(Exception, match="Failed to download CodeQL"):
                self.installer.download_codeql("v2.22.1")

        # Verify temp directory was cleaned up
        for temp_dir in temp_dirs:
            assert not Path(temp_dir).exists()

    def test_extract_codeql_creates_install_directory(self) -> None:
        """Test that extract_codeql creates the install directory."""
        # Create a dummy tar file
        tar_path = self.temp_dir / "test.tar.gz"

        # Create a simple tar file with a codeql/codeql structure
        source_dir = self.temp_dir / "source"
        source_dir.mkdir()
        codeql_dir = source_dir / "codeql"
        codeql_dir.mkdir()
        binary_file = codeql_dir / "codeql"
        binary_file.touch()

        # Create tar file
        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add(codeql_dir, arcname="codeql")

        # Test installation directory
        install_dir = self.temp_dir / "install"
        installer = CodeQLInstaller(str(install_dir))

        installer.extract_codeql(tar_path)

        assert install_dir.exists()
        assert (install_dir / "codeql" / "codeql").exists()
        assert os.access(install_dir / "codeql" / "codeql", os.X_OK)

    def test_extract_codeql_fails_when_binary_missing(self) -> None:
        """Test that extract_codeql fails when CodeQL binary is not found
        after extraction."""
        # Create a dummy tar file without the codeql binary
        tar_path = self.temp_dir / "test.tar.gz"

        # Create a simple tar file without codeql/codeql structure
        source_dir = self.temp_dir / "source"
        source_dir.mkdir()
        dummy_file = source_dir / "dummy.txt"
        dummy_file.touch()

        # Create tar file
        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add(dummy_file, arcname="dummy.txt")

        # Test installation directory
        install_dir = self.temp_dir / "install"
        installer = CodeQLInstaller(str(install_dir))

        with pytest.raises(Exception, match="CodeQL binary not found after extraction"):
            installer.extract_codeql(tar_path)

    @patch.object(CodeQLInstaller, "download_codeql")
    @patch.object(CodeQLInstaller, "extract_codeql")
    @patch.object(CodeQLInstaller, "is_installed")
    @patch.object(CodeQLInstaller, "get_version")
    def test_install_with_force_removes_existing(
        self, mock_get_version, mock_is_installed, mock_extract, mock_download
    ) -> None:
        """Test install with force=True removes existing installation."""
        # Create existing installation
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        existing_file = self.temp_dir / "existing.txt"
        existing_file.touch()

        # Mock download to return a fake tar path
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            fake_tar = Path(tmp_file.name)
        mock_download.return_value = fake_tar

        # Mock installation check
        # Already installed, then still installed
        mock_is_installed.side_effect = [True, True]
        mock_get_version.return_value = "2.22.1"

        try:
            result = self.installer.install("v2.22.1", force=True)

            assert result == str(self.installer.codeql_binary)
            mock_download.assert_called_once_with("v2.22.1")
            mock_extract.assert_called_once_with(fake_tar)
            # Verify existing file was removed
            assert not existing_file.exists()
        finally:
            # Clean up
            if fake_tar.exists():
                fake_tar.unlink()

    @patch.object(CodeQLInstaller, "download_codeql")
    @patch.object(CodeQLInstaller, "extract_codeql")
    @patch.object(CodeQLInstaller, "is_installed")
    def test_install_fails_verification(
        self, mock_is_installed, mock_extract, mock_download
    ) -> None:
        """Test install fails when verification fails."""
        # Mock download to return a fake tar path
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            fake_tar = Path(tmp_file.name)
        mock_download.return_value = fake_tar

        # Mock installation check - not installed before, still not installed after
        mock_is_installed.side_effect = [False, False]

        try:
            with pytest.raises(
                Exception, match="CodeQL installation verification failed"
            ):
                self.installer.install("v2.22.1")
        finally:
            # Clean up
            if fake_tar.exists():
                fake_tar.unlink()

    def test_uninstall_handles_permission_error(self) -> None:
        """Test uninstall handles permission errors gracefully."""
        # Create installation directory with a file
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        test_file = self.temp_dir / "test.txt"
        test_file.touch()

        # Mock shutil.rmtree to raise PermissionError
        with patch("shutil.rmtree", side_effect=PermissionError("Permission denied")):
            with pytest.raises(Exception, match="Failed to uninstall CodeQL"):
                self.installer.uninstall()

    def test_get_platform_unknown(self) -> None:
        """Test get_platform with unknown platform through URL generation."""
        from unittest.mock import patch

        with patch("platform.system", return_value="unknown"), patch(
            "platform.machine", return_value="unknown"
        ):
            url = self.installer.get_download_url("v2.22.1")
            # Should default to linux64
            assert "linux64" in url

    def test_get_platform_windows(self) -> None:
        """Test get_platform for Windows through URL generation."""
        from unittest.mock import patch

        with patch("platform.system", return_value="Windows"):
            url = self.installer.get_download_url("v2.22.1")
            assert "win64" in url

    def test_get_platform_macos(self) -> None:
        """Test get_platform for macOS through URL generation."""
        from unittest.mock import patch

        with patch("platform.system", return_value="Darwin"):
            url = self.installer.get_download_url("v2.22.1")
            assert "osx64" in url

    def test_install_network_error(self) -> None:
        """Test install with network error during download."""
        from unittest.mock import patch
        from urllib.error import URLError

        with patch(
            "codeql_wrapper.infrastructure.codeql_installer.urlretrieve"
        ) as mock_urlretrieve:
            mock_urlretrieve.side_effect = URLError("Network error")

            with pytest.raises(Exception, match="Failed to download CodeQL"):
                self.installer.install()

    def test_get_version_not_installed(self) -> None:
        """Test get_version when CodeQL is not installed."""
        # When not installed, get_version should return None
        version = self.installer.get_version()
        assert version is None

    def test_install_with_existing_directory_force_false(self) -> None:
        """Test install when directory exists and force=False."""
        from unittest.mock import patch

        # Create existing codeql directory with binary
        codeql_dir = self.temp_dir / "codeql"
        codeql_dir.mkdir(parents=True)
        binary_path = codeql_dir / "codeql"
        binary_path.touch()
        binary_path.chmod(0o755)

        # Mock the version check to avoid execution errors
        with patch.object(self.installer, "get_version", return_value="2.22.1"):
            # Should return existing path when force=False and already installed
            result = self.installer.install(force=False)
            assert str(result) == str(binary_path)
