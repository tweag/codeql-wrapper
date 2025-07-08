"""Tests for the CLI module."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from click.testing import CliRunner

from src.codeql_wrapper.cli import cli


class TestCLI:
    """Test cases for the CLI interface."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_cli_no_arguments_shows_help(self) -> None:
        """Test CLI with no arguments shows help."""
        result = self.runner.invoke(cli, [])

        assert result.exit_code == 0
        assert (
            "A universal Python CLI wrapper for running CodeQL analysis"
            in result.output
        )
        assert "analyze" in result.output
        assert "install" in result.output
        assert "--verbose" in result.output

    def test_cli_help(self) -> None:
        """Test CLI help output."""
        result = self.runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert (
            "A universal Python CLI wrapper for running CodeQL analysis"
            in result.output
        )
        assert "analyze" in result.output
        assert "install" in result.output
        assert "--verbose" in result.output

    def test_cli_version(self) -> None:
        """Test CLI version output."""
        from src.codeql_wrapper import __version__

        result = self.runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert __version__ in result.output

    def test_analyze_command_help(self) -> None:
        """Test analyze command help output."""
        result = self.runner.invoke(cli, ["analyze", "--help"])

        assert result.exit_code == 0
        assert "Run CodeQL analysis on a repository" in result.output
        assert "--languages" in result.output
        assert "--output-dir" in result.output
        assert "--force-install" in result.output

    def test_install_command_help(self) -> None:
        """Test install command help output."""
        result = self.runner.invoke(cli, ["install", "--help"])

        assert result.exit_code == 0
        assert "Install CodeQL CLI" in result.output
        assert "--force" in result.output
        assert "--version" in result.output
        # Check that version uses -V, not -v to avoid conflict with global verbose
        assert "-V" in result.output

    def test_analyze_command_requires_repository_path(self) -> None:
        """Test analyze command requires repository path."""
        result = self.runner.invoke(cli, ["analyze"])

        assert result.exit_code == 2  # Click usage error
        assert "Missing argument" in result.output

    @patch("src.codeql_wrapper.cli.CodeQLAnalysisUseCase")
    def test_analyze_command_with_valid_path(self, mock_use_case_class) -> None:
        """Test analyze command with valid repository path."""
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the use case
            mock_use_case = Mock()
            mock_summary = Mock()
            mock_summary.repository_path = Path(temp_dir)
            mock_summary.detected_projects = []
            mock_summary.successful_analyses = 0
            mock_summary.analysis_results = []
            mock_summary.success_rate = 1.0
            mock_summary.total_findings = 0
            mock_summary.failed_analyses = 0
            mock_use_case.execute.return_value = mock_summary
            mock_use_case_class.return_value = mock_use_case

            result = self.runner.invoke(cli, ["analyze", temp_dir])

            assert result.exit_code == 0
            mock_use_case.execute.assert_called_once()

    @patch("src.codeql_wrapper.cli.CodeQLAnalysisUseCase")
    def test_analyze_command_with_languages_option(self, mock_use_case_class) -> None:
        """Test analyze command with languages option."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the use case
            mock_use_case = Mock()
            mock_summary = Mock()
            mock_summary.repository_path = Path(temp_dir)
            mock_summary.detected_projects = []
            mock_summary.successful_analyses = 0
            mock_summary.analysis_results = []
            mock_summary.success_rate = 1.0
            mock_summary.total_findings = 0
            mock_summary.failed_analyses = 0
            mock_use_case.execute.return_value = mock_summary
            mock_use_case_class.return_value = mock_use_case

            result = self.runner.invoke(
                cli, ["analyze", temp_dir, "--languages", "python,javascript"]
            )

            assert result.exit_code == 0
            # Check that the request was created with the right languages
            call_args = mock_use_case.execute.call_args[0][0]
            assert call_args.target_languages is not None
            assert len(call_args.target_languages) == 2

    @patch("src.codeql_wrapper.infrastructure.codeql_installer.CodeQLInstaller")
    def test_install_command_success(self, mock_installer_class) -> None:
        """Test install command success."""
        mock_installer = Mock()
        mock_installer.is_installed.return_value = False
        mock_installer.install.return_value = "/path/to/codeql"
        mock_installer.get_version.return_value = "2.22.1"
        mock_installer_class.return_value = mock_installer

        result = self.runner.invoke(cli, ["install"])

        assert result.exit_code == 0
        assert "✅ CodeQL 2.22.1 installed successfully!" in result.output
        mock_installer.install.assert_called_once()

    @patch("src.codeql_wrapper.infrastructure.codeql_installer.CodeQLInstaller")
    def test_install_command_already_installed(self, mock_installer_class) -> None:
        """Test install command when already installed."""
        mock_installer = Mock()
        mock_installer.is_installed.return_value = True
        mock_installer.get_version.return_value = "2.22.1"
        mock_installer.get_binary_path.return_value = "/path/to/codeql"
        mock_installer_class.return_value = mock_installer

        result = self.runner.invoke(cli, ["install"])

        assert result.exit_code == 0
        assert "✅ CodeQL is already installed" in result.output
        mock_installer.install.assert_not_called()

    @patch("src.codeql_wrapper.infrastructure.codeql_installer.CodeQLInstaller")
    def test_install_command_with_force(self, mock_installer_class) -> None:
        """Test install command with force flag."""
        mock_installer = Mock()
        mock_installer.is_installed.return_value = True
        mock_installer.install.return_value = "/path/to/codeql"
        mock_installer.get_version.return_value = "2.22.1"
        mock_installer_class.return_value = mock_installer

        result = self.runner.invoke(cli, ["install", "--force"])

        assert result.exit_code == 0
        assert "🔄 Force reinstalling CodeQL..." in result.output
        mock_installer.install.assert_called_once_with(version="v2.22.1", force=True)

    @patch("src.codeql_wrapper.infrastructure.codeql_installer.CodeQLInstaller")
    def test_install_command_custom_version(self, mock_installer_class) -> None:
        """Test install command with custom version."""
        mock_installer = Mock()
        mock_installer.is_installed.return_value = False
        mock_installer.install.return_value = "/path/to/codeql"
        mock_installer.get_version.return_value = "2.20.0"
        mock_installer_class.return_value = mock_installer

        result = self.runner.invoke(cli, ["install", "--version", "v2.20.0"])

        assert result.exit_code == 0
        mock_installer.install.assert_called_once_with(version="v2.20.0", force=False)

    def test_verbose_flag_global(self) -> None:
        """Test that verbose flag works globally."""
        result = self.runner.invoke(cli, ["--verbose", "--help"])

        assert result.exit_code == 0
        # The verbose flag should be processed without error

    def test_analyze_with_nonexistent_path(self) -> None:
        """Test analyze command with non-existent path."""
        result = self.runner.invoke(cli, ["analyze", "/nonexistent/path"])

        assert result.exit_code == 2  # Click validation error
        assert "does not exist" in result.output.lower()

    @patch("src.codeql_wrapper.cli.CodeQLAnalysisUseCase")
    def test_analyze_command_handles_exception(self, mock_use_case_class) -> None:
        """Test analyze command handles exceptions gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the use case to raise an exception
            mock_use_case = Mock()
            mock_use_case.execute.side_effect = Exception("Test error")
            mock_use_case_class.return_value = mock_use_case

            result = self.runner.invoke(cli, ["analyze", temp_dir])

            assert result.exit_code == 1
            assert "Error: Test error" in result.output

    @patch("src.codeql_wrapper.infrastructure.codeql_installer.CodeQLInstaller")
    def test_install_command_handles_exception(self, mock_installer_class) -> None:
        """Test install command handles exceptions gracefully."""
        mock_installer = Mock()
        mock_installer.is_installed.side_effect = Exception("Install error")
        mock_installer_class.return_value = mock_installer

        result = self.runner.invoke(cli, ["install"])

        assert result.exit_code == 1
        assert "❌ Installation failed: Install error" in result.output

    @patch("src.codeql_wrapper.cli.CodeQLAnalysisUseCase")
    def test_analyze_command_unsupported_language(self, mock_use_case_class) -> None:
        """Test analyze command with unsupported language."""
        import tempfile

        # Create a temporary repository directory
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            (repo_path / "main.py").write_text("print('hello')")

            # Mock the use case to avoid actual analysis
            mock_use_case = Mock()
            mock_summary = Mock()
            mock_summary.repository_path = Path(temp_dir)
            mock_summary.detected_projects = []
            mock_summary.successful_analyses = 0
            mock_summary.analysis_results = []
            mock_summary.success_rate = 1.0
            mock_summary.total_findings = 0
            mock_summary.failed_analyses = 0
            mock_use_case.execute.return_value = mock_summary
            mock_use_case_class.return_value = mock_use_case

            result = self.runner.invoke(
                cli,
                ["analyze", str(repo_path), "--languages", "unsupported-lang,python"],
            )

            assert result.exit_code == 0
            assert "Unsupported language: unsupported-lang" in result.output

    def test_analyze_command_with_failures(self) -> None:
        """Test analyze command output when there are failures."""
        import tempfile
        from unittest.mock import patch, Mock

        # Create a temporary repository directory
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            (repo_path / "main.py").write_text("print('hello')")

            # Mock the use case to return failures
            mock_use_case = Mock()
            mock_summary = Mock()
            mock_summary.total_findings = 0
            mock_summary.total_projects = 1
            mock_summary.successful_analyses = 0
            mock_summary.failed_analyses = 1
            mock_summary.success_rate = 0.0
            mock_summary.repository_path = str(repo_path)
            mock_summary.detected_projects = ["test-project"]

            # Create a mock failed result
            mock_result = Mock()
            mock_result.is_successful = False
            mock_result.project_info.name = "test-project"
            mock_result.error_message = "Analysis failed"
            mock_result.output_files = None
            mock_summary.analysis_results = [mock_result]

            # Set up the mock use case to return the summary when execute is called
            mock_use_case.execute.return_value = mock_summary

            with patch(
                "src.codeql_wrapper.cli.CodeQLAnalysisUseCase",
                return_value=mock_use_case,
            ):
                result = self.runner.invoke(cli, ["analyze", str(repo_path)])

            # The CLI should succeed even with failed analyses -
            # it only exits with error code on exceptions
            assert result.exit_code == 0
            assert "1 analysis(es) failed" in result.output
            assert "test-project: Analysis failed" in result.output

    def test_upload_sarif_command_help(self) -> None:
        """Test upload-sarif command help output."""
        result = self.runner.invoke(cli, ["upload-sarif", "--help"])

        assert result.exit_code == 0
        assert "Upload SARIF file to GitHub Code Scanning" in result.output
        assert "--repository" in result.output
        assert "--commit-sha" in result.output
        assert "--github-token" in result.output

    def test_upload_sarif_command_requires_arguments(self) -> None:
        """Test upload-sarif command requires required arguments."""
        # Test missing SARIF file
        result = self.runner.invoke(cli, ["upload-sarif"])
        assert result.exit_code == 2
        assert "Missing argument" in result.output

    @patch("src.codeql_wrapper.cli.SarifUploadUseCase")
    def test_upload_sarif_command_success(self, mock_use_case_class) -> None:
        """Test upload-sarif command success."""
        import tempfile

        # Create a temporary SARIF file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sarif", delete=False) as f:
            f.write('{"version": "2.1.0", "runs": []}')
            sarif_file = f.name

        try:
            # Mock the use case
            mock_use_case = Mock()
            mock_result = Mock()
            mock_result.success = True
            mock_result.successful_uploads = 1
            mock_result.failed_uploads = 0
            mock_result.errors = None
            mock_use_case.execute.return_value = mock_result
            mock_use_case_class.return_value = mock_use_case

            result = self.runner.invoke(
                cli,
                [
                    "upload-sarif",
                    sarif_file,
                    "--repository",
                    "owner/repo",
                    "--commit-sha",
                    "abc123",
                    "--github-token",
                    "token",
                ],
            )

            assert result.exit_code == 0
            assert "Successfully uploaded SARIF file" in result.output
            mock_use_case.execute.assert_called_once()

        finally:
            import os

            os.unlink(sarif_file)

    @patch("src.codeql_wrapper.cli.SarifUploadUseCase")
    def test_analyze_command_with_upload_sarif(
        self, mock_upload_use_case_class
    ) -> None:
        """Test analyze command with SARIF upload enabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a mock SARIF file
            sarif_file = Path(temp_dir) / "results.sarif"
            sarif_file.write_text('{"version": "2.1.0", "runs": []}')

            # Mock the analysis use case
            mock_analysis_use_case = Mock()
            mock_summary = Mock()
            mock_summary.repository_path = Path(temp_dir)
            mock_summary.detected_projects = []
            mock_summary.successful_analyses = 1
            mock_summary.analysis_results = []
            mock_summary.success_rate = 1.0
            mock_summary.total_findings = 0
            mock_summary.failed_analyses = 0

            # Create a mock result with SARIF files
            mock_result = Mock()
            mock_result.output_files = [sarif_file]
            mock_summary.analysis_results = [mock_result]

            mock_analysis_use_case.execute.return_value = mock_summary

            # Mock the upload use case
            mock_upload_use_case = Mock()
            mock_upload_result = Mock()
            mock_upload_result.success = True
            mock_upload_result.successful_uploads = 1
            mock_upload_result.failed_uploads = 0
            mock_upload_result.errors = None
            mock_upload_use_case.execute.return_value = mock_upload_result
            mock_upload_use_case_class.return_value = mock_upload_use_case

            with patch(
                "src.codeql_wrapper.cli.CodeQLAnalysisUseCase",
                return_value=mock_analysis_use_case,
            ):
                result = self.runner.invoke(
                    cli,
                    [
                        "analyze",
                        temp_dir,
                        "--upload-sarif",
                        "--repository",
                        "owner/repo",
                        "--commit-sha",
                        "abc123",
                        "--github-token",
                        "token",
                    ],
                )

            assert result.exit_code == 0
            assert "Successfully uploaded 1 SARIF file(s)" in result.output

    def test_analyze_command_upload_sarif_validation(self) -> None:
        """Test analyze command validates required parameters for SARIF upload."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test missing repository
            result = self.runner.invoke(
                cli,
                [
                    "analyze",
                    temp_dir,
                    "--upload-sarif",
                    "--commit-sha",
                    "abc123",
                    "--github-token",
                    "token",
                ],
            )
            assert result.exit_code == 1
            assert "--repository is required when using --upload-sarif" in result.output

            # Test missing commit-sha
            result = self.runner.invoke(
                cli,
                [
                    "analyze",
                    temp_dir,
                    "--upload-sarif",
                    "--repository",
                    "owner/repo",
                    "--github-token",
                    "token",
                ],
            )
            assert result.exit_code == 1
            assert "--commit-sha is required when using --upload-sarif" in result.output

            # Test missing github-token
            result = self.runner.invoke(
                cli,
                [
                    "analyze",
                    temp_dir,
                    "--upload-sarif",
                    "--repository",
                    "owner/repo",
                    "--commit-sha",
                    "abc123",
                ],
            )
            assert result.exit_code == 1
            assert "GitHub token is required when using --upload-sarif" in result.output
