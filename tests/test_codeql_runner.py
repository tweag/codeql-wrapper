"""Tests for the CodeQL runner infrastructure module."""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from codeql_wrapper.infrastructure.codeql_runner import CodeQLRunner, CodeQLResult


class TestCodeQLResult:
    """Test cases for the CodeQLResult dataclass."""

    def test_codeql_result_creation(self) -> None:
        """Test CodeQLResult creation with all fields."""
        result = CodeQLResult(
            success=True,
            stdout="output",
            stderr="",
            exit_code=0,
            command=["codeql", "version"],
        )

        assert result.success is True
        assert result.stdout == "output"
        assert result.stderr == ""
        assert result.exit_code == 0
        assert result.command == ["codeql", "version"]

    def test_codeql_result_failure(self) -> None:
        """Test CodeQLResult for failed command."""
        result = CodeQLResult(
            success=False,
            stdout="",
            stderr="error message",
            exit_code=1,
            command=["codeql", "invalid"],
        )

        assert result.success is False
        assert result.stdout == ""
        assert result.stderr == "error message"
        assert result.exit_code == 1
        assert result.command == ["codeql", "invalid"]


class TestCodeQLRunner:
    """Test cases for the CodeQL runner."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.fake_codeql_path = str(self.temp_dir / "codeql")

        # Create fake codeql binary
        Path(self.fake_codeql_path).touch()

        self.runner = CodeQLRunner(codeql_path=self.fake_codeql_path)

    def teardown_method(self) -> None:
        """Clean up test fixtures."""
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_runner_initialization_with_path(self) -> None:
        """Test runner initialization with explicit CodeQL path."""
        runner = CodeQLRunner(codeql_path="/custom/path/codeql")
        assert runner._codeql_path == "/custom/path/codeql"

    @patch("codeql_wrapper.infrastructure.codeql_runner.CodeQLInstaller")
    def test_runner_initialization_without_path(self, mock_installer_class) -> None:
        """Test runner initialization without explicit CodeQL path."""
        mock_installer = Mock()
        mock_installer.get_binary_path.return_value = "/auto/detected/codeql"
        mock_installer_class.return_value = mock_installer

        runner = CodeQLRunner()
        assert runner._codeql_path is None
        assert runner.codeql_path == "/auto/detected/codeql"

    @patch("codeql_wrapper.infrastructure.codeql_runner.CodeQLInstaller")
    def test_codeql_path_raises_when_not_found(self, mock_installer_class) -> None:
        """Test that codeql_path raises exception when CodeQL not found."""
        mock_installer = Mock()
        mock_installer.get_binary_path.return_value = None
        mock_installer_class.return_value = mock_installer

        runner = CodeQLRunner()
        with pytest.raises(Exception, match="CodeQL not found"):
            _ = runner.codeql_path

    @patch("subprocess.run")
    def test_run_command_success(self, mock_run) -> None:
        """Test successful command execution."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "success output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = self.runner._run_command(["version"])

        assert result.success is True
        assert result.stdout == "success output"
        assert result.stderr == ""
        assert result.exit_code == 0
        assert result.command == [self.fake_codeql_path, "version"]

    @patch("subprocess.run")
    def test_run_command_failure(self, mock_run) -> None:
        """Test failed command execution."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error message"
        mock_run.return_value = mock_result

        result = self.runner._run_command(["invalid"])

        assert result.success is False
        assert result.stdout == ""
        assert result.stderr == "error message"
        assert result.exit_code == 1
        assert result.command == [self.fake_codeql_path, "invalid"]

    @patch("subprocess.run")
    def test_run_command_timeout(self, mock_run) -> None:
        """Test command timeout handling."""
        mock_run.side_effect = subprocess.TimeoutExpired("codeql", 300)

        result = self.runner._run_command(["long-running"])

        assert result.success is False
        assert result.stderr == "Command timed out after 5 minutes"
        assert result.exit_code == -1

    @patch("subprocess.run")
    def test_run_command_exception(self, mock_run) -> None:
        """Test command execution exception handling."""
        mock_run.side_effect = Exception("Subprocess error")

        result = self.runner._run_command(["error"])

        assert result.success is False
        assert result.stderr == "Subprocess error"
        assert result.exit_code == -1

    @patch("subprocess.run")
    def test_version(self, mock_run) -> None:
        """Test version command."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '{"productVersion": "2.22.1"}'
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = self.runner.version()

        assert result.success is True
        assert '{"productVersion": "2.22.1"}' in result.stdout
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args == [self.fake_codeql_path, "version", "--format=json"]

    @patch("subprocess.run")
    def test_resolve_languages(self, mock_run) -> None:
        """Test resolve languages command."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "language: javascript\nlanguage: python"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = self.runner.resolve_languages("/source")

        assert result.success is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args == [
            self.fake_codeql_path,
            "resolve",
            "languages",
            "--source-root",
            "/source",
        ]

    @patch("subprocess.run")
    def test_create_database_minimal(self, mock_run) -> None:
        """Test database creation with minimal parameters."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Database created"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = self.runner.create_database("/db", "/source", "javascript")

        assert result.success is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        expected = [
            self.fake_codeql_path,
            "database",
            "create",
            "/db",
            "--source-root",
            "/source",
            "--language",
            "javascript",
        ]
        assert args == expected

    @patch("subprocess.run")
    def test_create_database_with_command(self, mock_run) -> None:
        """Test database creation with build command."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Database created"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = self.runner.create_database(
            "/db", "/source", "java", command="mvn compile", overwrite=True
        )

        assert result.success is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        expected = [
            self.fake_codeql_path,
            "database",
            "create",
            "/db",
            "--source-root",
            "/source",
            "--language",
            "java",
            "--command",
            "mvn compile",
            "--overwrite",
        ]
        assert args == expected

    @patch("subprocess.run")
    def test_analyze_database_minimal(self, mock_run) -> None:
        """Test database analysis with minimal parameters."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Analysis complete"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = self.runner.analyze_database("/db")

        assert result.success is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        expected = [
            self.fake_codeql_path,
            "database",
            "analyze",
            "/db",
            "--format=sarif-latest",
        ]
        assert args == expected

    @patch("subprocess.run")
    def test_analyze_database_with_output(self, mock_run) -> None:
        """Test database analysis with output file."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Analysis complete"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = self.runner.analyze_database("/db", output="/results.csv")

        assert result.success is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        expected = [
            self.fake_codeql_path,
            "database",
            "analyze",
            "/db",
            "--format=csv",
            "--output",
            "/results.csv",
        ]
        assert args == expected

    @patch("subprocess.run")
    def test_run_query(self, mock_run) -> None:
        """Test running a specific query."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Query results"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = self.runner.run_query(
            "/db", "/query.ql", output_format="json", output="/results.json"
        )

        assert result.success is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        expected = [
            self.fake_codeql_path,
            "query",
            "run",
            "/query.ql",
            "--database",
            "/db",
            "--format=json",
            "--output",
            "/results.json",
        ]
        assert args == expected

    @patch("subprocess.run")
    def test_pack_download(self, mock_run) -> None:
        """Test downloading a CodeQL pack."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Pack downloaded"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = self.runner.pack_download("codeql/javascript-all", "/target")

        assert result.success is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        expected = [
            self.fake_codeql_path,
            "pack",
            "download",
            "codeql/javascript-all",
            "--dir",
            "/target",
        ]
        assert args == expected

    @patch("subprocess.run")
    def test_database_finalize(self, mock_run) -> None:
        """Test database finalization."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Database finalized"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = self.runner.database_finalize("/db")

        assert result.success is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        expected = [self.fake_codeql_path, "database", "finalize", "/db"]
        assert args == expected

    @patch("subprocess.run")
    def test_database_cleanup(self, mock_run) -> None:
        """Test database cleanup."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Database cleaned"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = self.runner.database_cleanup("/db")

        assert result.success is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        expected = [self.fake_codeql_path, "database", "cleanup", "/db"]
        assert args == expected

    @patch("subprocess.run")
    def test_get_supported_languages_success(self, mock_run) -> None:
        """Test getting supported languages successfully."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "language: javascript\nlanguage: python\nlanguage: java"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        languages = self.runner.get_supported_languages()

        assert "javascript" in languages
        assert "python" in languages
        assert "java" in languages

    @patch("subprocess.run")
    def test_get_supported_languages_failure(self, mock_run) -> None:
        """Test getting supported languages when command fails."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error"
        mock_run.return_value = mock_result

        languages = self.runner.get_supported_languages()

        assert languages == []

    @patch("subprocess.run")
    def test_get_supported_languages_parse_error(self, mock_run) -> None:
        """Test getting supported languages with parse error."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "invalid output format"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        languages = self.runner.get_supported_languages()

        assert languages == []

    @patch("subprocess.run")
    @patch("tempfile.mkdtemp")
    @patch("pathlib.Path.exists")
    def test_create_and_analyze_success(
        self, mock_exists, mock_mkdtemp, mock_run
    ) -> None:
        """Test create and analyze in one step - success case."""
        mock_mkdtemp.return_value = "/tmp/test123"
        mock_exists.return_value = True  # Database path exists for cleanup

        # Mock successful database creation
        create_result = Mock()
        create_result.returncode = 0
        create_result.stdout = "Database created"
        create_result.stderr = ""

        # Mock successful analysis
        analyze_result = Mock()
        analyze_result.returncode = 0
        analyze_result.stdout = "Analysis complete"
        analyze_result.stderr = ""

        mock_run.side_effect = [create_result, analyze_result]

        # Use cleanup_database=False to avoid the shutil cleanup
        result = self.runner.create_and_analyze(
            "/source",
            "javascript",
            "/results.sarif",
            build_command="npm install",
            cleanup_database=False,
        )

        assert result.success is True
        assert mock_run.call_count == 2

    @patch("subprocess.run")
    @patch("tempfile.mkdtemp")
    def test_create_and_analyze_database_creation_fails(
        self, mock_mkdtemp, mock_run
    ) -> None:
        """Test create and analyze when database creation fails."""
        mock_mkdtemp.return_value = "/tmp/test123"

        # Mock failed database creation
        create_result = Mock()
        create_result.returncode = 1
        create_result.stdout = ""
        create_result.stderr = "Database creation failed"

        mock_run.return_value = create_result

        result = self.runner.create_and_analyze(
            "/source", "javascript", "/results.sarif"
        )

        assert result.success is False
        assert result.stderr == "Database creation failed"
        assert mock_run.call_count == 1  # Only create was called, not analyze

    @patch("subprocess.run")
    @patch("tempfile.mkdtemp")
    @patch("pathlib.Path.exists")
    def test_create_and_analyze_analysis_fails(
        self, mock_exists, mock_mkdtemp, mock_run
    ) -> None:
        """Test create and analyze when analysis fails."""
        mock_mkdtemp.return_value = "/tmp/test123"
        mock_exists.return_value = True  # Database path exists for cleanup

        # Mock successful database creation
        create_result = Mock()
        create_result.returncode = 0
        create_result.stdout = "Database created"
        create_result.stderr = ""

        # Mock failed analysis
        analyze_result = Mock()
        analyze_result.returncode = 1
        analyze_result.stdout = ""
        analyze_result.stderr = "Analysis failed"

        mock_run.side_effect = [create_result, analyze_result]

        # Use cleanup_database=False to avoid the shutil cleanup
        result = self.runner.create_and_analyze(
            "/source", "javascript", "/results.sarif", cleanup_database=False
        )

        assert result.success is False
        assert result.stderr == "Analysis failed"
        assert mock_run.call_count == 2

    @patch("subprocess.run")
    def test_create_and_analyze_with_custom_database_path(self, mock_run) -> None:
        """Test create and analyze with custom database path."""
        # Mock successful database creation and analysis
        success_result = Mock()
        success_result.returncode = 0
        success_result.stdout = "Success"
        success_result.stderr = ""

        mock_run.return_value = success_result

        result = self.runner.create_and_analyze(
            "/source",
            "javascript",
            "/results.sarif",
            database_name="/custom/db/path",
            cleanup_database=False,
        )

        assert result.success is True
        assert mock_run.call_count == 2

        # Check that the custom database path was used
        create_call_args = mock_run.call_args_list[0][0][0]
        assert "/custom/db/path" in create_call_args
