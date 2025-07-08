"""Tests for the CodeQL analysis use case module.

This module contains comprehensive tests for the CodeQLAnalysisUseCase class,
including both unit tests for individual methods and integration tests for
the complete analysis workflow.
"""

from unittest.mock import Mock, patch
from pathlib import Path
import pytest

from codeql_wrapper.domain.use_cases.codeql_analysis_use_case import (
    CodeQLAnalysisUseCase,
)
from codeql_wrapper.domain.entities.codeql_analysis import (
    CodeQLAnalysisRequest,
    CodeQLLanguage,
    ProjectInfo,
    AnalysisStatus,
    CodeQLInstallationInfo,
)


class TestCodeQLAnalysisUseCase:
    """Test cases for the CodeQL analysis use case."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.mock_logger = Mock()
        self.use_case = CodeQLAnalysisUseCase(self.mock_logger)

    def test_init(self) -> None:
        """Test use case initialization."""
        assert self.use_case._logger == self.mock_logger
        assert self.use_case._language_detector is not None
        assert self.use_case._codeql_installer is not None

    def test_execute_with_basic_request(self) -> None:
        """Test execute method with a basic analysis request."""
        # Create analysis request with proper path mocking
        with patch("pathlib.Path.exists", return_value=True), patch(
            "pathlib.Path.is_dir", return_value=True
        ):
            request = CodeQLAnalysisRequest(
                repository_path=Path("/test/repo"),
                target_languages=None,
                output_directory=Path("/test/output"),
                verbose=False,
                force_install=False,
            )

        # Mock all the internal methods to avoid complex setup
        with patch.object(
            self.use_case, "_verify_codeql_installation"
        ) as mock_verify, patch.object(
            self.use_case, "_detect_projects"
        ) as mock_detect_projects, patch.object(
            self.use_case, "_analyze_project"
        ) as mock_analyze_project:

            # Setup verification mock
            mock_verify.return_value = CodeQLInstallationInfo(
                is_installed=True, version="2.22.1", path=Path("/path/to/codeql")
            )

            # Setup project detection mock with path validation
            with patch("pathlib.Path.exists", return_value=True):
                mock_detect_projects.return_value = [
                    ProjectInfo(
                        name="repo",
                        path=Path("/test/repo"),
                        languages={CodeQLLanguage.PYTHON},
                    )
                ]

            # Setup analysis mock
            from codeql_wrapper.domain.entities.codeql_analysis import (
                CodeQLAnalysisResult,
            )
            from datetime import datetime

            with patch("pathlib.Path.exists", return_value=True):
                mock_analyze_project.return_value = CodeQLAnalysisResult(
                    project_info=ProjectInfo(
                        name="repo",
                        path=Path("/test/repo"),
                        languages={CodeQLLanguage.PYTHON},
                    ),
                    status=AnalysisStatus.COMPLETED,
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    output_files=[Path("/test/output/results.sarif")],
                    findings_count=5,
                    error_message=None,
                )

            # Execute the use case
            result = self.use_case.execute(request)

            # Verify results
            assert result is not None
            assert result.repository_path == Path("/test/repo")
            assert len(result.detected_projects) == 1
            assert result.successful_analyses == 1
            assert result.total_findings == 5
            assert result.success_rate == 1.0

    def test_request_validation_in_constructor(self) -> None:
        """Test request validation happens in constructor."""
        # Test that invalid paths are caught during object creation
        with pytest.raises(ValueError, match="Repository path does not exist"):
            CodeQLAnalysisRequest(
                repository_path=Path("/nonexistent/path"),
                target_languages={CodeQLLanguage.PYTHON},
                output_directory=Path("/test/output"),
                verbose=False,
                force_install=False,
            )

    @patch("codeql_wrapper.domain.use_cases.codeql_analysis_use_case.CodeQLInstaller")
    @patch("codeql_wrapper.domain.use_cases.codeql_analysis_use_case.CodeQLRunner")
    def test_verify_codeql_installation_already_installed(
        self, mock_runner_class, mock_installer_class
    ) -> None:
        """Test CodeQL installation check when already installed."""
        mock_installer = Mock()
        mock_installer_class.return_value = mock_installer
        mock_installer.is_installed.return_value = True
        mock_installer.get_version.return_value = "2.22.1"
        mock_installer.get_binary_path.return_value = "/path/to/codeql"

        # Mock CodeQL runner for version check
        mock_runner = Mock()
        mock_runner_class.return_value = mock_runner
        mock_version_result = Mock()
        mock_version_result.success = True
        mock_version_result.stdout = '{"version": "2.22.1"}'
        mock_runner.version.return_value = mock_version_result

        use_case = CodeQLAnalysisUseCase(self.mock_logger)

        installation_info = use_case._verify_codeql_installation(force_install=False)

        assert installation_info.version == "2.22.1"
        assert installation_info.path == Path("/path/to/codeql")
        assert installation_info.is_installed is True

        # Should not call install if already installed and not forced
        mock_installer.install.assert_not_called()

    @patch("codeql_wrapper.domain.use_cases.codeql_analysis_use_case.CodeQLInstaller")
    @patch("codeql_wrapper.domain.use_cases.codeql_analysis_use_case.CodeQLRunner")
    def test_verify_codeql_installation_force_install(
        self, mock_runner_class, mock_installer_class
    ) -> None:
        """Test CodeQL installation with force install."""
        mock_installer = Mock()
        mock_installer_class.return_value = mock_installer
        mock_installer.is_installed.return_value = True
        mock_installer.get_version.return_value = "2.22.1"
        mock_installer.get_binary_path.return_value = "/path/to/codeql"
        mock_installer.install.return_value = "/path/to/codeql"

        # Mock CodeQL runner for version check
        mock_runner = Mock()
        mock_runner_class.return_value = mock_runner
        mock_version_result = Mock()
        mock_version_result.success = True
        mock_version_result.stdout = '{"version": "2.22.1"}'
        mock_runner.version.return_value = mock_version_result

        use_case = CodeQLAnalysisUseCase(self.mock_logger)

        installation_info = use_case._verify_codeql_installation(force_install=True)

        assert installation_info.version == "2.22.1"
        assert installation_info.path == Path("/path/to/codeql")
        assert installation_info.is_installed is True

        # Should call install when forced
        mock_installer.install.assert_called_once()

    def test_verify_codeql_installation_not_found(self) -> None:
        """Test CodeQL installation verification when not found."""
        with patch.object(
            self.use_case._codeql_installer, "get_binary_path"
        ) as mock_get_path, patch.object(
            self.use_case._codeql_installer, "is_installed"
        ) as mock_is_installed, patch.object(
            self.use_case._codeql_installer, "install"
        ) as mock_install:
            # Setup mock to return None (not found)
            mock_get_path.return_value = None
            mock_is_installed.return_value = False
            # Make install fail with a simple error message
            mock_install.side_effect = Exception("CodeQL binary not found")

            # Execute
            result = self.use_case._verify_codeql_installation()

            # Verify
            assert result.is_installed is False
            assert result.error_message is not None
            assert "CodeQL binary not found" in result.error_message
            assert result.is_valid is False

    def test_filter_projects_by_languages(self) -> None:
        """Test filtering projects by target languages."""
        # Create test projects with path mocking
        with patch("pathlib.Path.exists", return_value=True):
            projects = [
                ProjectInfo(
                    name="python-project",
                    path=Path("/test/python"),
                    languages={CodeQLLanguage.PYTHON},
                ),
                ProjectInfo(
                    name="js-project",
                    path=Path("/test/js"),
                    languages={CodeQLLanguage.JAVASCRIPT},
                ),
                ProjectInfo(
                    name="mixed-project",
                    path=Path("/test/mixed"),
                    languages={CodeQLLanguage.PYTHON, CodeQLLanguage.JAVASCRIPT},
                ),
            ]

            # Test filtering for Python only
            filtered = self.use_case._filter_projects_by_language(
                projects, {CodeQLLanguage.PYTHON}
            )

            assert len(filtered) == 2  # python-project and mixed-project
            project_names = {p.name for p in filtered}
            assert "python-project" in project_names
            assert "mixed-project" in project_names
            assert "js-project" not in project_names

    def test_filter_projects_by_languages_no_filter(self) -> None:
        """Test filtering projects with no language filter (should return all)."""
        # Create test projects with path mocking
        with patch("pathlib.Path.exists", return_value=True):
            projects = [
                ProjectInfo(
                    name="python-project",
                    path=Path("/test/python"),
                    languages={CodeQLLanguage.PYTHON},
                ),
                ProjectInfo(
                    name="js-project",
                    path=Path("/test/js"),
                    languages={CodeQLLanguage.JAVASCRIPT},
                ),
            ]

            # Test with None filter (should return all projects)
            filtered = self.use_case._filter_projects_by_language(projects, None)

            assert len(filtered) == 2
            assert filtered == projects

    def test_detect_projects_with_python(self) -> None:
        """Test project detection with Python files."""
        # Create a temporary directory structure
        with patch.object(
            self.use_case._language_detector, "detect_all_languages"
        ) as mock_detect, patch("pathlib.Path.exists", return_value=True):

            # Mock language detection
            mock_detect.return_value = {"non_compiled": ["python"], "compiled": []}

            # Create test path
            test_path = Path("/test/repo")

            # Execute
            projects = self.use_case._detect_projects(test_path)

            # Verify
            assert len(projects) == 1
            project = projects[0]
            assert project.name == "repo"
            assert CodeQLLanguage.PYTHON in project.languages
            assert project.primary_language == CodeQLLanguage.PYTHON

    def test_detect_projects_with_javascript_and_python(self) -> None:
        """Test project detection with multiple languages."""
        with patch.object(
            self.use_case._language_detector, "detect_all_languages"
        ) as mock_detect, patch("pathlib.Path.exists", return_value=True):

            # Mock language detection
            mock_detect.return_value = {
                "non_compiled": ["javascript", "python"],
                "compiled": [],
            }

            test_path = Path("/test/repo")

            # Execute
            projects = self.use_case._detect_projects(test_path)

            # Verify
            assert len(projects) == 1
            project = projects[0]
            assert CodeQLLanguage.JAVASCRIPT in project.languages
            assert CodeQLLanguage.PYTHON in project.languages
            # JavaScript has higher priority than Python
            assert project.primary_language == CodeQLLanguage.JAVASCRIPT

    def test_determine_primary_language_priority(self) -> None:
        """Test primary language determination based on priority."""
        languages = {CodeQLLanguage.PYTHON, CodeQLLanguage.TYPESCRIPT}

        # Execute
        primary = self.use_case._determine_primary_language(languages)

        # Verify - TypeScript has higher priority than Python
        assert primary == CodeQLLanguage.TYPESCRIPT

    def test_determine_primary_language_empty(self) -> None:
        """Test primary language determination with empty set."""
        languages = set()

        # Execute
        primary = self.use_case._determine_primary_language(languages)

        # Verify - should return None for empty set
        assert primary is None

    @patch("builtins.open")
    @patch("json.load")
    def test_count_sarif_findings(self, mock_json_load: Mock, mock_open: Mock) -> None:
        """Test SARIF findings counting."""
        # Mock SARIF content
        mock_sarif_data = {
            "runs": [
                {
                    "results": [
                        {"ruleId": "rule1", "level": "error"},
                        {"ruleId": "rule2", "level": "warning"},
                    ]
                }
            ]
        }
        mock_json_load.return_value = mock_sarif_data

        # Execute
        count = self.use_case._count_sarif_findings(Path("/test/results.sarif"))

        # Verify
        assert count == 2
        mock_open.assert_called_once_with(Path("/test/results.sarif"), "r")

    @patch("builtins.open")
    @patch("json.load")
    def test_count_sarif_findings_file_error(
        self, mock_json_load: Mock, mock_open: Mock
    ) -> None:
        """Test counting SARIF findings when file read fails."""
        # Mock file operations to raise an exception
        mock_open.side_effect = FileNotFoundError("File not found")

        findings_count = self.use_case._count_sarif_findings(Path("/nonexistent.sarif"))

        assert findings_count == 0
        mock_open.assert_called_once()

    def test_analyze_project_full_workflow(self) -> None:
        """Test the complete _analyze_project workflow."""
        from unittest.mock import patch, Mock
        import tempfile

        # Create a temporary directory for the test
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test-project"
            project_path.mkdir()
            repo_path = Path(temp_dir) / "test-repo"
            repo_path.mkdir()
            output_path = Path(temp_dir) / "test-output"
            output_path.mkdir()

            # Create a project info
            project = ProjectInfo(
                name="test-project",
                path=project_path,
                languages={CodeQLLanguage.PYTHON},
            )

            # Create a request
            request = CodeQLAnalysisRequest(
                repository_path=repo_path,
                target_languages=None,
                output_directory=output_path,
                verbose=False,
                force_install=False,
            )

            # Mock CodeQL runner and all necessary methods
            mock_runner = Mock()
            mock_runner.create_and_analyze.return_value = Mock(success=True)

            self.use_case._codeql_runner = mock_runner

            # Mock _export_codeql_suites_path to avoid path issues
            with patch.object(
                self.use_case, "_export_codeql_suites_path"
            ), patch.object(self.use_case, "_count_sarif_findings", return_value=5):
                result = self.use_case._analyze_project(project, request)

            assert result.project_info == project
            assert result.status == AnalysisStatus.COMPLETED
            assert result.findings_count == 5
            assert result.error_message is None

    def test_analyze_project_failure(self) -> None:
        """Test _analyze_project when CodeQL analysis fails."""
        from unittest.mock import Mock, patch
        import tempfile

        # Create a temporary directory for the test
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test-project"
            project_path.mkdir()
            repo_path = Path(temp_dir) / "test-repo"
            repo_path.mkdir()
            output_path = Path(temp_dir) / "test-output"
            output_path.mkdir()

            project = ProjectInfo(
                name="test-project",
                path=project_path,
                languages={CodeQLLanguage.PYTHON},
            )

            request = CodeQLAnalysisRequest(
                repository_path=repo_path,
                target_languages=None,
                output_directory=output_path,
                verbose=False,
                force_install=False,
            )

            # Mock CodeQL runner to fail
            mock_runner = Mock()
            mock_runner.create_and_analyze.return_value = Mock(
                success=False, stderr="Database creation and analysis failed"
            )

            self.use_case._codeql_runner = mock_runner

            # Mock _export_codeql_suites_path to avoid path issues
            with patch.object(self.use_case, "_export_codeql_suites_path"):
                result = self.use_case._analyze_project(project, request)

            assert result.project_info == project
            assert result.status == AnalysisStatus.FAILED
            assert result.findings_count == 0
            assert (
                result.error_message is not None
                and "Database creation and analysis failed" in result.error_message
            )

        self.use_case._codeql_runner = mock_runner

        result = self.use_case._analyze_project(project, request)

        assert result.status == AnalysisStatus.FAILED
        assert result.error_message is not None
        assert "Analysis failed" in result.error_message

    def test_export_codeql_suites_path(self) -> None:
        """Test _export_codeql_suites_path method."""
        from unittest.mock import patch, Mock
        import tempfile
        from pathlib import Path

        # Mock the runner with a valid codeql path
        mock_runner = Mock()

        with tempfile.TemporaryDirectory() as temp_dir:
            codeql_root = Path(temp_dir) / "codeql"
            codeql_root.mkdir()

            # Create bin directory
            bin_dir = codeql_root / "bin"
            bin_dir.mkdir()

            # Create qlpacks directory under bin
            # (since that's where the algorithm looks)
            qlpacks_dir = bin_dir / "qlpacks"
            qlpacks_dir.mkdir()

            # Create a language directory under bin
            python_dir = bin_dir / "python"
            python_dir.mkdir()

            # Set the mock runner to use the codeql binary path
            mock_runner.codeql_path = str(bin_dir / "codeql")

            with patch.object(self.use_case, "_codeql_runner", mock_runner), patch(
                "os.environ", {}
            ) as mock_env:
                self.use_case._export_codeql_suites_path()

                # Verify the environment variables were set
                assert mock_env.get("CODEQL_DIST") == str(bin_dir)
                assert "CODEQL_REPO" in mock_env
                # Should contain both qlpacks and python directories
                codeql_repo = mock_env.get("CODEQL_REPO")
                assert codeql_repo is not None
                assert str(qlpacks_dir) in codeql_repo
                assert str(python_dir) in codeql_repo

    def test_verify_codeql_installation_auto_install(self) -> None:
        """Test _verify_codeql_installation when auto-install is needed."""
        from unittest.mock import patch, Mock

        mock_installer = Mock()
        mock_installer.get_binary_path.return_value = None  # Not installed
        mock_installer.install.return_value = "/path/to/codeql"

        # Mock CodeQLRunner to return successful version check
        mock_runner_class = Mock()
        mock_runner_instance = Mock()
        mock_version_result = Mock()
        mock_version_result.success = True
        mock_version_result.stdout = '{"version": "2.22.1"}'
        mock_runner_instance.version.return_value = mock_version_result
        mock_runner_class.return_value = mock_runner_instance

        with patch.object(self.use_case, "_codeql_installer", mock_installer), patch(
            "codeql_wrapper.domain.use_cases.codeql_analysis_use_case.CodeQLRunner",
            mock_runner_class,
        ):
            info = self.use_case._verify_codeql_installation(force_install=False)

        assert info.is_valid
        assert info.version == "2.22.1"
        mock_installer.install.assert_called_once_with(force=False)

    def test_verify_codeql_installation_install_failure(self) -> None:
        """Test _verify_codeql_installation when install fails."""
        from unittest.mock import patch, Mock

        mock_installer = Mock()
        mock_installer.get_binary_path.return_value = None  # Not installed
        mock_installer.install.side_effect = Exception("Install failed")

        with patch.object(self.use_case, "_codeql_installer", mock_installer):
            info = self.use_case._verify_codeql_installation(force_install=False)

        assert not info.is_valid
        assert (
            info.error_message is not None
            and "Failed to install CodeQL: Install failed" in info.error_message
        )

    def test_verify_codeql_installation_force_install_failure(self) -> None:
        """Test _verify_codeql_installation when force reinstall fails."""
        from unittest.mock import patch, Mock

        mock_installer = Mock()
        mock_installer.get_binary_path.return_value = (
            "/existing/path"  # Already installed
        )
        mock_installer.install.side_effect = Exception("Reinstall failed")

        with patch.object(self.use_case, "_codeql_installer", mock_installer):
            info = self.use_case._verify_codeql_installation(force_install=True)

        assert not info.is_valid
        assert (
            info.error_message is not None
            and "Failed to reinstall CodeQL: Reinstall failed" in info.error_message
        )

    def test_verify_codeql_installation_version_check_failure(self) -> None:
        """Test _verify_codeql_installation when version check fails."""
        from unittest.mock import patch, Mock

        mock_installer = Mock()
        mock_installer.get_binary_path.return_value = "/path/to/codeql"

        # Mock CodeQLRunner to return failed version check
        mock_runner_class = Mock()
        mock_runner_instance = Mock()
        mock_version_result = Mock()
        mock_version_result.success = False
        mock_version_result.stderr = "Version command failed"
        mock_runner_instance.version.return_value = mock_version_result
        mock_runner_class.return_value = mock_runner_instance

        with patch.object(self.use_case, "_codeql_installer", mock_installer), patch(
            "codeql_wrapper.domain.use_cases.codeql_analysis_use_case.CodeQLRunner",
            mock_runner_class,
        ):
            info = self.use_case._verify_codeql_installation(force_install=False)

        assert not info.is_valid
        assert (
            info.error_message is not None
            and "Failed to get CodeQL version: Version command failed"
            in info.error_message
        )

    def test_count_sarif_findings_from_file(self) -> None:
        """Test _count_sarif_findings method."""
        import tempfile
        import json

        # Create a temporary SARIF file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sarif", delete=False) as f:
            sarif_data = {
                "runs": [
                    {
                        "results": [
                            {"ruleId": "rule1", "message": {"text": "Finding 1"}},
                            {"ruleId": "rule2", "message": {"text": "Finding 2"}},
                        ]
                    },
                    {
                        "results": [
                            {"ruleId": "rule3", "message": {"text": "Finding 3"}}
                        ]
                    },
                ]
            }
            json.dump(sarif_data, f)
            sarif_file = Path(f.name)

        try:
            count = self.use_case._count_sarif_findings(sarif_file)
            assert count == 3
        finally:
            sarif_file.unlink()

    def test_count_sarif_findings_invalid_file(self) -> None:
        """Test _count_sarif_findings with invalid file."""
        import tempfile

        # Create a temporary non-JSON file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sarif", delete=False) as f:
            f.write("invalid json")
            sarif_file = Path(f.name)

        try:
            count = self.use_case._count_sarif_findings(sarif_file)
            assert count == 0  # Should return 0 on error
        finally:
            sarif_file.unlink()

    def test_count_sarif_findings_missing_file(self) -> None:
        """Test _count_sarif_findings with missing file."""
        missing_file = Path("/nonexistent/file.sarif")
        count = self.use_case._count_sarif_findings(missing_file)
        assert count == 0  # Should return 0 on error

    def test_analyze_project_exception_handling(self) -> None:
        """Test _analyze_project exception handling."""
        from unittest.mock import patch
        import tempfile

        # Create a temporary directory for the test
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test-project"
            project_path.mkdir()
            repo_path = Path(temp_dir) / "test-repo"
            repo_path.mkdir()
            output_path = Path(temp_dir) / "test-output"
            output_path.mkdir()

            project = ProjectInfo(
                name="test-project",
                path=project_path,
                languages={CodeQLLanguage.PYTHON},
            )

            request = CodeQLAnalysisRequest(
                repository_path=repo_path,
                target_languages=None,
                output_directory=output_path,
                verbose=False,
                force_install=False,
            )

            # Mock _export_codeql_suites_path to raise an exception
            with patch.object(
                self.use_case,
                "_export_codeql_suites_path",
                side_effect=Exception("Unexpected error"),
            ):
                result = self.use_case._analyze_project(project, request)

            assert result.status == AnalysisStatus.FAILED
            assert result.error_message is not None
            assert "Unexpected error" in result.error_message

    def test_verify_codeql_installation_forced(self) -> None:
        """Test _verify_codeql_installation with force install."""
        from unittest.mock import patch, Mock

        mock_installer = Mock()
        mock_installer.is_installed.return_value = True
        mock_installer.install.return_value = "/path/to/codeql"
        mock_installer.get_binary_path.return_value = "/path/to/codeql"
        mock_installer.get_version.return_value = "2.22.1"

        # Mock CodeQLRunner to return successful version check
        mock_runner_class = Mock()
        mock_runner_instance = Mock()
        mock_version_result = Mock()
        mock_version_result.success = True
        mock_version_result.stdout = '{"version": "2.22.1"}'
        mock_runner_instance.version.return_value = mock_version_result
        mock_runner_class.return_value = mock_runner_instance

        with patch.object(self.use_case, "_codeql_installer", mock_installer), patch(
            "codeql_wrapper.domain.use_cases.codeql_analysis_use_case.CodeQLRunner",
            mock_runner_class,
        ):
            info = self.use_case._verify_codeql_installation(force_install=True)

        assert info.is_valid
        assert info.version == "2.22.1"
        assert str(info.path) == "/path/to/codeql"
        mock_installer.install.assert_called_once_with(force=True)

    def test_determine_primary_language_with_priorities(self) -> None:
        """Test _determine_primary_language with different language priorities."""
        # Test with high priority languages - JavaScript has higher priority than Java
        languages = {
            CodeQLLanguage.JAVA,
            CodeQLLanguage.PYTHON,
            CodeQLLanguage.JAVASCRIPT,
        }
        result = self.use_case._determine_primary_language(languages)
        # JavaScript should have higher priority than Java and Python
        assert result == CodeQLLanguage.JAVASCRIPT

        # Test with only compiled languages
        languages = {CodeQLLanguage.CPP, CodeQLLanguage.CSHARP}
        result = self.use_case._determine_primary_language(languages)
        # Should return one of them (order defined by implementation)
        assert result in {CodeQLLanguage.CPP, CodeQLLanguage.CSHARP}

        # Test with mixed compiled and non-compiled
        languages = {CodeQLLanguage.PYTHON, CodeQLLanguage.GO}
        result = self.use_case._determine_primary_language(languages)
        # Python has higher priority than Go in the implementation
        assert result == CodeQLLanguage.PYTHON
