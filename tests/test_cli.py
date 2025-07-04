"""Tests for the CLI module."""

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
            "A clean Python CLI application for CodeQL wrapper functionality"
            in result.output
        )
        assert "USE_CASE: The use case to execute" in result.output
        assert "--verbose" in result.output

    @patch("codeql_wrapper.cli.HelloWorldUseCase")
    @patch("codeql_wrapper.cli.get_logger")
    @patch("codeql_wrapper.cli.configure_logging")
    def test_cli_hello_world_use_case(
        self, mock_configure_logging, mock_get_logger, mock_use_case_class
    ) -> None:
        """Test CLI with hello-world use case."""
        # Setup mocks
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        mock_use_case = Mock()
        mock_response = Mock()
        mock_response.message = "Hello, World!"
        mock_use_case.execute.return_value = mock_response
        mock_use_case_class.return_value = mock_use_case

        # Execute
        result = self.runner.invoke(cli, ["hello-world"])

        # Assert
        assert result.exit_code == 0
        assert "Hello, World!" in result.output

        # Verify mocks were called correctly
        mock_configure_logging.assert_called_once_with(verbose=False)
        mock_use_case_class.assert_called_once_with(mock_logger)
        mock_use_case.execute.assert_called_once_with("World")

    @patch("codeql_wrapper.cli.HelloWorldUseCase")
    @patch("codeql_wrapper.cli.get_logger")
    @patch("codeql_wrapper.cli.configure_logging")
    def test_cli_hello_world_with_verbose(
        self, mock_configure_logging, mock_get_logger, mock_use_case_class
    ) -> None:
        """Test CLI with hello-world use case and verbose flag."""
        # Setup mocks
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        mock_use_case = Mock()
        mock_response = Mock()
        mock_response.message = "Hello, World!"
        mock_use_case.execute.return_value = mock_response
        mock_use_case_class.return_value = mock_use_case

        # Execute
        result = self.runner.invoke(cli, ["hello-world", "--verbose"])

        # Assert
        assert result.exit_code == 0
        assert "Hello, World!" in result.output

        # Verify verbose flag was passed
        mock_configure_logging.assert_called_once_with(verbose=True)

    def test_cli_unknown_use_case(self) -> None:
        """Test CLI with unknown use case."""
        result = self.runner.invoke(cli, ["unknown-case"])

        assert result.exit_code == 1
        assert "Error: Unknown use case 'unknown-case'" in result.output
        assert "Available use cases: hello-world" in result.output

    @patch("codeql_wrapper.cli.HelloWorldUseCase")
    @patch("codeql_wrapper.cli.get_logger")
    @patch("codeql_wrapper.cli.configure_logging")
    def test_cli_hello_world_with_value_error(
        self, mock_configure_logging, mock_get_logger, mock_use_case_class
    ) -> None:
        """Test CLI handling of ValueError in hello-world use case."""
        # Setup mocks
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        mock_use_case = Mock()
        mock_use_case.execute.side_effect = ValueError("Invalid input")
        mock_use_case_class.return_value = mock_use_case

        # Execute
        result = self.runner.invoke(cli, ["hello-world"])

        # Assert
        assert result.exit_code == 1
        assert "Error: Invalid input" in result.output

    def test_cli_help(self) -> None:
        """Test CLI help output."""
        result = self.runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert (
            "A clean Python CLI application for CodeQL wrapper functionality"
            in result.output
        )
        assert "USE_CASE" in result.output
        assert "--verbose" in result.output

    def test_cli_version(self) -> None:
        """Test CLI version output."""
        result = self.runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "0.1.0" in result.output
