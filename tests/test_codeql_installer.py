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

    def test_is_installed_false_when_not_executable(self) -> None:
        """Test is_installed returns False when binary is not executable."""
        installer = CodeQLInstaller(install_dir=str(self.temp_dir))

        # Create the binary file but make it not executable
        installer.codeql_binary.parent.mkdir(parents=True, exist_ok=True)
        installer.codeql_binary.touch()

        # Make it not executable (Unix-like systems)
        with patch("platform.system", return_value="Linux"):
            with patch("os.access", return_value=False):
                assert installer.is_installed() is False

    def test_is_installed_windows_executable_check(self) -> None:
        """Test is_installed on Windows always returns True if file exists."""
        installer = CodeQLInstaller(install_dir=str(self.temp_dir))

        # Create the binary file
        installer.codeql_binary.parent.mkdir(parents=True, exist_ok=True)
        installer.codeql_binary.touch()

        # On Windows, just check if file exists
        with patch("platform.system", return_value="Windows"):
            assert installer.is_installed() is True

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

    def test_installer_initialization_default_dir(self) -> None:
        """Test installer initialization with default directory."""
        default_installer = CodeQLInstaller()
        expected_path = Path.home() / ".codeql"
        assert default_installer.install_dir == expected_path
        assert default_installer.codeql_binary == expected_path / "codeql" / "codeql"

    def test_installer_initialization_custom_dir(self) -> None:
        """Test installer initialization with custom directory."""
        custom_dir = str(self.temp_dir / "custom_codeql")
        installer = CodeQLInstaller(install_dir=custom_dir)

        assert installer.install_dir == Path(custom_dir)
        expected_binary = Path(custom_dir) / "codeql" / "codeql"
        assert installer.codeql_binary == expected_binary

    def test_installer_initialization_invalid_dir_file(self) -> None:
        """Test installer initialization with invalid directory (file path)."""
        # Create a file instead of directory
        file_path = self.temp_dir / "invalid_file.txt"
        file_path.write_text("test")

        with pytest.raises(ValueError, match="Install directory cannot be a file"):
            CodeQLInstaller(install_dir=str(file_path))

    def test_get_download_url_different_versions(self) -> None:
        """Test download URL generation for different versions."""
        test_cases = [
            ("v2.14.6", "codeql-bundle-v2.14.6"),
            ("v2.16.0", "codeql-bundle-v2.16.0"),
        ]

        # Test non-latest versions (no network calls)
        for version_input, expected_in_url in test_cases:
            url = self.installer.get_download_url(version_input)
            # Test should work on both macOS and Linux
            assert expected_in_url in url
            assert url.endswith(".tar.gz")
            assert "github.com/github/codeql-action/releases/download" in url

        # Test "latest" version with mocked get_latest_version
        with patch.object(
            self.installer, "get_latest_version", return_value="codeql-bundle-v2.22.1"
        ):
            url = self.installer.get_download_url("latest")
            assert "codeql-bundle-v2.22.1" in url
            assert url.endswith(".tar.gz")
            assert "github.com/github/codeql-action/releases/download" in url

    def test_get_download_url_different_version_formats(self) -> None:
        """Test download URL generation with different version formats."""
        installer = CodeQLInstaller()

        # Test with version already in bundle format
        url = installer.get_download_url("codeql-bundle-v2.22.1")
        assert "codeql-bundle-v2.22.1" in url

        # Test with version needing 'v' prefix
        url = installer.get_download_url("2.22.1")
        assert "codeql-bundle-v2.22.1" in url

        # Test with version already having 'v' prefix
        url = installer.get_download_url("v2.22.1")
        assert "codeql-bundle-v2.22.1" in url

    def test_get_download_url_version_format_handling(self) -> None:
        """Test download URL generation with various version formats."""
        installer = CodeQLInstaller()

        # Test version without 'v' prefix
        with patch.object(
            installer, "get_platform_bundle_name", return_value="linux64"
        ):
            url = installer.get_download_url("2.22.1")
            assert "codeql-bundle-v2.22.1" in url
            assert "codeql-bundle-linux64.tar.gz" in url

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

        # Mock installation check - not installed before, still not installed
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
        """Test platform detection for macOS."""
        installer = CodeQLInstaller()

        with patch("platform.system", return_value="Darwin"):
            platform_name = installer.get_platform_bundle_name()
            assert platform_name == "osx64"

    def test_get_platform_unknown_system(self) -> None:
        """Test platform detection for unknown system."""
        installer = CodeQLInstaller()

        with patch("platform.system", return_value="FreeBSD"):
            with patch("platform.machine", return_value="x86_64"):
                platform_name = installer.get_platform_bundle_name()
                assert platform_name == "linux64"  # Default fallback

    def test_install_network_error(self) -> None:
        """Test install with network error during download."""
        from unittest.mock import patch
        from urllib.error import URLError

        # Mock get_latest_version to avoid hitting GitHub API
        with patch.object(self.installer, "get_latest_version", return_value="v2.22.1"):
            with patch(
                "codeql_wrapper.infrastructure.codeql_installer.urlretrieve"
            ) as mock_urlretrieve:
                mock_urlretrieve.side_effect = URLError("Network error")

                # Test with network error during download
                with pytest.raises(Exception, match="Failed to download CodeQL"):
                    self.installer.install(version="v2.22.1")

    def test_get_version_not_installed(self) -> None:
        """Test get_version when CodeQL is not installed."""
        # When not installed, get_version should return None
        version = self.installer.get_version()
        assert version is None

    def test_get_latest_version_success(self) -> None:
        """Test successful fetching of latest version from GitHub API."""
        # Mock urlopen at the module level where it's imported
        with patch(
            "codeql_wrapper.infrastructure.codeql_installer.urlopen"
        ) as mock_urlopen:
            # Mock the HTTP response
            mock_response = Mock()
            mock_response.status = 200
            mock_response.read.return_value = json.dumps(
                {"tag_name": "codeql-bundle-v2.23.0"}
            ).encode("utf-8")

            # Set up the context manager properly
            mock_urlopen.return_value.__enter__ = Mock(return_value=mock_response)
            mock_urlopen.return_value.__exit__ = Mock(return_value=None)

            version = self.installer.get_latest_version()

            # Should return the mocked version
            assert version == "codeql-bundle-v2.23.0"
            mock_urlopen.assert_called_once_with(
                "https://api.github.com/repos/github/codeql-action/releases/latest"
            )

    def test_get_latest_version_raises_on_http_error(self) -> None:
        """Test get_latest_version raises exception on HTTP error status."""
        with patch(
            "codeql_wrapper.infrastructure.codeql_installer.urlopen"
        ) as mock_urlopen:
            # Mock the HTTP response with error status
            mock_response = Mock()
            mock_response.status = 404

            # Set up the context manager properly
            mock_urlopen.return_value.__enter__ = Mock(return_value=mock_response)
            mock_urlopen.return_value.__exit__ = Mock(return_value=None)

            # Should raise an exception
            with pytest.raises(Exception, match="GitHub API returned status 404"):
                self.installer.get_latest_version()

            mock_urlopen.assert_called_once_with(
                "https://api.github.com/repos/github/codeql-action/releases/latest"
            )

    def test_get_latest_version_raises_on_invalid_json(self) -> None:
        """Test get_latest_version raises exception on invalid JSON response."""
        with patch(
            "codeql_wrapper.infrastructure.codeql_installer.urlopen"
        ) as mock_urlopen:
            # Mock the HTTP response with invalid JSON
            mock_response = Mock()
            mock_response.status = 200
            mock_response.read.return_value = b"invalid json"

            # Set up the context manager properly
            mock_urlopen.return_value.__enter__ = Mock(return_value=mock_response)
            mock_urlopen.return_value.__exit__ = Mock(return_value=None)

            # Should raise an exception
            with pytest.raises(
                Exception, match="Unable to fetch latest CodeQL version"
            ):
                self.installer.get_latest_version()

            mock_urlopen.assert_called_once_with(
                "https://api.github.com/repos/github/codeql-action/releases/latest"
            )

    def test_get_latest_version_raises_on_error(self) -> None:
        """Test get_latest_version raises exception on network error."""
        # Mock urlopen to raise an exception
        with patch(
            "codeql_wrapper.infrastructure.codeql_installer.urlopen"
        ) as mock_urlopen:
            from urllib.error import URLError

            mock_urlopen.side_effect = URLError("Network error")

            # Should raise an exception
            with pytest.raises(
                Exception, match="Unable to fetch latest CodeQL version"
            ):
                self.installer.get_latest_version()

            mock_urlopen.assert_called_once_with(
                "https://api.github.com/repos/github/codeql-action/releases/latest"
            )

    def test_get_download_url_with_none_version(self) -> None:
        """Test get_download_url calls get_latest_version when version is None."""
        with patch.object(
            self.installer, "get_latest_version", return_value="v2.23.0"
        ) as mock_get_latest:
            url = self.installer.get_download_url(None)

            mock_get_latest.assert_called_once()
            assert "codeql-bundle-v2.23.0" in url

    def test_download_codeql_with_none_version(self) -> None:
        """Test download_codeql calls get_latest_version when version is None."""
        with patch.object(
            self.installer, "get_latest_version", return_value="v2.23.0"
        ) as mock_get_latest:
            with patch(
                "codeql_wrapper.infrastructure.codeql_installer.urlretrieve"
            ) as mock_urlretrieve:

                def mock_download(url, path):
                    Path(path).touch()

                mock_urlretrieve.side_effect = mock_download

                result_path = self.installer.download_codeql(None)

                mock_get_latest.assert_called_once()
                assert "codeql-bundle-v2.23.0.tar.gz" in str(result_path)

    def test_install_with_none_version(self) -> None:
        """Test install calls get_latest_version when version is None."""
        with patch.object(
            self.installer, "get_latest_version", return_value="v2.23.0"
        ) as mock_get_latest:
            with patch.object(self.installer, "download_codeql") as mock_download:
                with patch.object(self.installer, "extract_codeql") as mock_extract:
                    with patch.object(
                        self.installer, "is_installed"
                    ) as mock_is_installed:
                        with patch.object(
                            self.installer, "get_version"
                        ) as mock_get_version_installed:
                            # Mock download to return a fake tar path
                            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                                fake_tar = Path(tmp_file.name)
                            mock_download.return_value = fake_tar

                            # Mock installation check
                            mock_is_installed.side_effect = [
                                False,
                                True,
                            ]  # Not installed, then installed
                            mock_get_version_installed.return_value = "2.23.0"

                            try:
                                result = self.installer.install(None)

                                mock_get_latest.assert_called_once()
                                assert result == str(self.installer.codeql_binary)
                                mock_download.assert_called_once_with("v2.23.0")
                                mock_extract.assert_called_once_with(fake_tar)
                            finally:
                                # Clean up
                                if fake_tar.exists():
                                    fake_tar.unlink()

    def test_install_with_existing_directory_force_false(self) -> None:
        """Test install when directory exists and force=False."""
        from unittest.mock import patch

        # Create existing codeql directory with binary
        codeql_dir = self.temp_dir / "codeql"
        codeql_dir.mkdir(parents=True)
        binary_path = codeql_dir / "codeql"
        binary_path.touch()
        binary_path.chmod(0o755)

        # Mock both version check and get_latest_version to avoid any API calls
        with patch.object(self.installer, "get_version", return_value="2.22.1"):
            with patch.object(
                self.installer, "get_latest_version", return_value="v2.22.1"
            ):
                # Should return existing path when force=False and already installed
                result = self.installer.install(version="v2.22.1", force=False)
                assert str(result) == str(binary_path)

    def test_get_download_url_raises_on_api_error(self) -> None:
        """Test get_download_url raises exception when get_latest_version fails."""
        # Mock urlopen to fail so get_latest_version raises exception
        with patch(
            "codeql_wrapper.infrastructure.codeql_installer.urlopen"
        ) as mock_urlopen:
            from urllib.error import URLError

            mock_urlopen.side_effect = URLError("Network error")

            # Should raise an exception
            with pytest.raises(
                Exception, match="Unable to fetch latest CodeQL version"
            ):
                self.installer.get_download_url(None)

    def test_download_codeql_raises_on_api_error(self) -> None:
        """Test download_codeql raises exception when get_latest_version fails."""
        # Mock urlopen to fail so get_latest_version raises exception
        with patch(
            "codeql_wrapper.infrastructure.codeql_installer.urlopen"
        ) as mock_urlopen:
            from urllib.error import URLError

            mock_urlopen.side_effect = URLError("Network error")

            # Should raise an exception
            with pytest.raises(
                Exception, match="Unable to fetch latest CodeQL version"
            ):
                self.installer.download_codeql(None)

    def test_install_raises_on_api_error(self) -> None:
        """Test install raises exception when get_latest_version fails."""
        # Mock urlopen to fail so get_latest_version raises exception
        with patch(
            "codeql_wrapper.infrastructure.codeql_installer.urlopen"
        ) as mock_urlopen:
            from urllib.error import URLError

            mock_urlopen.side_effect = URLError("Network error")

            # Should raise an exception
            with pytest.raises(
                Exception, match="Unable to fetch latest CodeQL version"
            ):
                self.installer.install(None)
