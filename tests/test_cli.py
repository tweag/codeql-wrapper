"""Tests for the CLI module."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from click.testing import CliRunner

from codeql_wrapper.cli import cli


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
        from codeql_wrapper import __version__

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

    @patch("codeql_wrapper.cli.CodeQLAnalysisUseCase")
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

    @patch("codeql_wrapper.cli.CodeQLAnalysisUseCase")
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

    @patch("codeql_wrapper.infrastructure.codeql_installer.CodeQLInstaller")
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

    @patch("codeql_wrapper.infrastructure.codeql_installer.CodeQLInstaller")
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

    @patch("codeql_wrapper.infrastructure.codeql_installer.CodeQLInstaller")
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

    @patch("codeql_wrapper.infrastructure.codeql_installer.CodeQLInstaller")
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

    @patch("codeql_wrapper.cli.CodeQLAnalysisUseCase")
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

    @patch("codeql_wrapper.infrastructure.codeql_installer.CodeQLInstaller")
    def test_install_command_handles_exception(self, mock_installer_class) -> None:
        """Test install command handles exceptions gracefully."""
        mock_installer = Mock()
        mock_installer.is_installed.side_effect = Exception("Install error")
        mock_installer_class.return_value = mock_installer

        result = self.runner.invoke(cli, ["install"])

        assert result.exit_code == 1
        assert "❌ Installation failed: Install error" in result.output

    @patch("codeql_wrapper.cli.CodeQLAnalysisUseCase")
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
                "codeql_wrapper.cli.CodeQLAnalysisUseCase", return_value=mock_use_case
            ):
                result = self.runner.invoke(cli, ["analyze", str(repo_path)])

            # The CLI should succeed even with failed analyses -
            # it only exits with error code on exceptions
            assert result.exit_code == 0
            assert "1 analysis(es) failed" in result.output
            assert "test-project: Analysis failed" in result.output
