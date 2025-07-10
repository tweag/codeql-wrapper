"""Tests for SARIF upload use case."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from codeql_wrapper.domain.entities.codeql_analysis import SarifUploadRequest
from codeql_wrapper.domain.use_cases.sarif_upload_use_case import SarifUploadUseCase


class TestSarifUploadUseCase:
    """Test cases for SARIF upload use case."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.use_case = SarifUploadUseCase()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_sample_sarif_file(self, filename: str = "test.sarif") -> Path:
        """Create a sample SARIF file for testing."""
        sarif_data = {
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {"driver": {"name": "CodeQL", "version": "2.22.1"}},
                    "results": [
                        {
                            "ruleId": "test-rule",
                            "message": {"text": "Test finding"},
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {"uri": "test.py"},
                                        "region": {"startLine": 1},
                                    }
                                }
                            ],
                        }
                    ],
                }
            ],
        }

        sarif_file = self.temp_dir / filename
        with open(sarif_file, "w") as f:
            json.dump(sarif_data, f)

        return sarif_file

    def test_create_request_validation(self):
        """Test request validation."""
        sarif_file = self._create_sample_sarif_file()

        # Valid request
        request = SarifUploadRequest(
            sarif_files=[sarif_file],
            repository="octocat/Hello-World",
            commit_sha="a1b2c3d4e5f6789012345678901234567890abcd",
            github_token="test-token",
            ref="refs/heads/main",
        )
        assert request.repository == "octocat/Hello-World"

        # Invalid repository format
        with pytest.raises(
            ValueError, match="Repository must be in 'owner/name' format"
        ):
            SarifUploadRequest(
                sarif_files=[sarif_file],
                repository="invalid-repo",
                commit_sha="a1b2c3d4e5f6789012345678901234567890abcd",
                github_token="test-token",
            )

        # Empty SARIF files
        with pytest.raises(ValueError, match="At least one SARIF file is required"):
            SarifUploadRequest(
                sarif_files=[],
                repository="octocat/Hello-World",
                commit_sha="a1b2c3d4e5f6789012345678901234567890abcd",
                github_token="test-token",
            )

    def test_request_validation_missing_fields(self):
        """Test request validation with missing required fields."""
        sarif_file = self._create_sample_sarif_file()

        # Missing repository
        with pytest.raises(
            ValueError, match="Repository must be in 'owner/name' format"
        ):
            request = SarifUploadRequest(
                sarif_files=[sarif_file],
                repository="",
                commit_sha="a1b2c3d4e5f6789012345678901234567890abcd",
                github_token="test-token",
            )
            self.use_case.execute(request)

        # Missing commit SHA
        with pytest.raises(ValueError, match="Commit SHA is required"):
            request = SarifUploadRequest(
                sarif_files=[sarif_file],
                repository="octocat/Hello-World",
                commit_sha="",
                github_token="test-token",
            )
            self.use_case.execute(request)

        # Missing GitHub token
        with pytest.raises(ValueError, match="GitHub token is required"):
            request = SarifUploadRequest(
                sarif_files=[sarif_file],
                repository="octocat/Hello-World",
                commit_sha="a1b2c3d4e5f6789012345678901234567890abcd",
                github_token="",
            )
            self.use_case.execute(request)

    def test_sarif_file_validation(self):
        """Test SARIF file validation."""
        # Non-existent file
        non_existent = self.temp_dir / "non_existent.sarif"
        with pytest.raises(ValueError, match="SARIF file does not exist"):
            request = SarifUploadRequest(
                sarif_files=[non_existent],
                repository="octocat/Hello-World",
                commit_sha="a1b2c3d4e5f6789012345678901234567890abcd",
                github_token="test-token",
            )
            self.use_case.execute(request)

        # Directory instead of file
        dir_path = self.temp_dir / "sarif_dir"
        dir_path.mkdir()
        with pytest.raises(ValueError, match="File is not a SARIF file"):
            request = SarifUploadRequest(
                sarif_files=[dir_path],
                repository="octocat/Hello-World",
                commit_sha="a1b2c3d4e5f6789012345678901234567890abcd",
                github_token="test-token",
            )
            self.use_case.execute(request)

    @patch(
        "codeql_wrapper.infrastructure.codeql_installer." "CodeQLInstaller.is_installed"
    )
    @patch(
        "codeql_wrapper.infrastructure.codeql_installer."
        "CodeQLInstaller.get_binary_path"
    )
    @patch("subprocess.run")
    def test_successful_upload(
        self, mock_subprocess, mock_get_binary, mock_is_installed
    ):
        """Test successful SARIF upload."""
        # Setup mocks
        mock_is_installed.return_value = True
        mock_get_binary.return_value = Path("/usr/local/bin/codeql")
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "Upload successful"
        mock_subprocess.return_value.stderr = ""

        # Create request
        sarif_file = self._create_sample_sarif_file()
        request = SarifUploadRequest(
            sarif_files=[sarif_file],
            repository="octocat/Hello-World",
            commit_sha="a1b2c3d4e5f6789012345678901234567890abcd",
            github_token="test-token",
            ref="refs/heads/main",
        )

        # Execute
        result = self.use_case.execute(request)

        # Verify
        assert result.success is True
        assert result.successful_uploads == 1
        assert result.failed_uploads == 0
        assert result.total_files == 1
        assert result.errors is None

    @patch(
        "codeql_wrapper.infrastructure.codeql_installer." "CodeQLInstaller.is_installed"
    )
    def test_codeql_not_installed(self, mock_is_installed):
        """Test error when CodeQL is not installed."""
        # Setup mock
        mock_is_installed.return_value = False

        # Create request
        sarif_file = self._create_sample_sarif_file()
        request = SarifUploadRequest(
            sarif_files=[sarif_file],
            repository="octocat/Hello-World",
            commit_sha="a1b2c3d4e5f6789012345678901234567890abcd",
            github_token="test-token",
        )

        # Execute
        result = self.use_case.execute(request)

        # Verify failure
        assert result.success is False
        assert result.failed_uploads == 1
        assert result.errors is not None
        assert "CodeQL CLI is not installed" in result.errors[0]

    @patch(
        "codeql_wrapper.infrastructure.codeql_installer." "CodeQLInstaller.is_installed"
    )
    @patch(
        "codeql_wrapper.infrastructure.codeql_installer."
        "CodeQLInstaller.get_binary_path"
    )
    @patch("subprocess.run")
    def test_upload_failure(self, mock_subprocess, mock_get_binary, mock_is_installed):
        """Test upload failure handling."""
        # Setup mocks
        mock_is_installed.return_value = True
        mock_get_binary.return_value = Path("/usr/local/bin/codeql")
        mock_subprocess.return_value.returncode = 1
        mock_subprocess.return_value.stdout = ""
        mock_subprocess.return_value.stderr = "Upload failed"

        # Create request
        sarif_file = self._create_sample_sarif_file()
        request = SarifUploadRequest(
            sarif_files=[sarif_file],
            repository="octocat/Hello-World",
            commit_sha="a1b2c3d4e5f6789012345678901234567890abcd",
            github_token="test-token",
        )

        # Execute
        result = self.use_case.execute(request)

        # Verify failure
        assert result.success is False
        assert result.successful_uploads == 0
        assert result.failed_uploads == 1
        assert result.total_files == 1
        assert result.errors is not None
        assert len(result.errors) == 1
        assert "Upload failed" in result.errors[0]

    @patch(
        "codeql_wrapper.infrastructure.codeql_installer." "CodeQLInstaller.is_installed"
    )
    @patch(
        "codeql_wrapper.infrastructure.codeql_installer."
        "CodeQLInstaller.get_binary_path"
    )
    @patch("subprocess.run")
    def test_mixed_upload_results(
        self, mock_subprocess, mock_get_binary, mock_is_installed
    ):
        """Test mixed upload results (some success, some failure)."""
        # Setup mocks
        mock_is_installed.return_value = True
        mock_get_binary.return_value = Path("/usr/local/bin/codeql")

        # First call succeeds, second fails
        success_result = type(
            "", (), {"returncode": 0, "stdout": "Upload successful", "stderr": ""}
        )()
        failure_result = type(
            "", (), {"returncode": 1, "stdout": "", "stderr": "Upload failed"}
        )()

        mock_subprocess.side_effect = [success_result, failure_result]

        # Create request with multiple files
        sarif_file1 = self._create_sample_sarif_file("test1.sarif")
        sarif_file2 = self._create_sample_sarif_file("test2.sarif")
        request = SarifUploadRequest(
            sarif_files=[sarif_file1, sarif_file2],
            repository="octocat/Hello-World",
            commit_sha="a1b2c3d4e5f6789012345678901234567890abcd",
            github_token="test-token",
        )

        # Execute
        result = self.use_case.execute(request)

        # Verify mixed results
        assert result.success is False  # Overall failure since not all succeeded
        assert result.successful_uploads == 1
        assert result.failed_uploads == 1
        assert result.total_files == 2
        assert result.errors is not None
        assert len(result.errors) == 1

    def test_use_case_initialization(self):
        """Test use case initialization."""
        # Test with default logger
        use_case = SarifUploadUseCase()
        assert use_case._installer is not None
        assert use_case._logger is not None

        # Test with custom logger
        import logging

        custom_logger = logging.getLogger("test")
        use_case = SarifUploadUseCase(custom_logger)
        assert use_case._logger is custom_logger
