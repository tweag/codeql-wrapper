"""Tests for the CLI module."""

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
        result = self.runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "0.1.0" in result.output

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

    def test_analyze_command_requires_repository_path(self) -> None:
        """Test analyze command requires repository path."""
        result = self.runner.invoke(cli, ["analyze"])

        assert result.exit_code == 2  # Click usage error
        assert "Missing argument" in result.output
