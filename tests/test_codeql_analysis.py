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
        """Test SARIF findings counting with file error."""
        # Mock file error
        mock_open.side_effect = FileNotFoundError("File not found")

        # Execute
        count = self.use_case._count_sarif_findings(Path("/test/missing.sarif"))

        # Verify - should return 0 on error
        assert count == 0
