"""CodeQL analysis use case implementation."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Set

from ..entities.codeql_analysis import (
    CodeQLAnalysisRequest,
    CodeQLAnalysisResult,
    CodeQLInstallationInfo,
    CodeQLLanguage,
    ProjectInfo,
    RepositoryAnalysisSummary,
    AnalysisStatus,
)
from ...infrastructure.language_detector import LanguageDetector
from ...infrastructure.codeql_installer import CodeQLInstaller
from ...infrastructure.codeql_runner import CodeQLRunner


class CodeQLAnalysisUseCase:
    """Use case for running CodeQL analysis on repositories."""

    def __init__(self, logger: Any) -> None:
        """Initialize the use case with dependencies."""
        self._logger = logger
        self._language_detector = LanguageDetector()
        self._codeql_installer = CodeQLInstaller()
        self._codeql_runner: Optional[CodeQLRunner] = None

    def execute(self, request: CodeQLAnalysisRequest) -> RepositoryAnalysisSummary:
        """
        Execute CodeQL analysis on a repository.

        Args:
            request: CodeQL analysis request

        Returns:
            RepositoryAnalysisSummary with analysis results

        Raises:
            ValueError: If the request is invalid
            Exception: If CodeQL installation or analysis fails
        """
        try:
            self._logger.info(
                f"Starting single repository CodeQL analysis for: "
                f"{request.repository_path}"
            )

            # Step 1: Verify CodeQL installation
            installation_info = self._verify_codeql_installation(request.force_install)
            if not installation_info.is_valid:
                raise Exception(
                    f"CodeQL installation error: {installation_info.error_message}"
                )

            # Step 2: Initialize CodeQL runner
            self._codeql_runner = CodeQLRunner(str(installation_info.path))

            # Step 3: Detect projects and languages
            detected_projects = self._detect_projects(request.repository_path)
            self._logger.info(f"Detected {len(detected_projects)} project(s)")

            # Step 4: Filter projects by target languages if specified
            filtered_projects = self._filter_projects_by_language(
                detected_projects, request.target_languages
            )

            # Step 5: Run analysis on each project
            analysis_results = []
            for project in filtered_projects:
                result = self._analyze_project(project, request)
                analysis_results.append(result)

            # Step 6: Create summary
            summary = RepositoryAnalysisSummary(
                repository_path=request.repository_path,
                detected_projects=detected_projects,
                analysis_results=analysis_results,
            )

            self._logger.info(
                f"Analysis completed. Success rate: {summary.success_rate:.2%} "
                f"({summary.successful_analyses}/{len(analysis_results)})"
            )

            return summary

        except Exception as e:
            self._logger.error(f"CodeQL analysis failed: {e}")
            raise

    def _verify_codeql_installation(
        self, force_install: bool = False
    ) -> CodeQLInstallationInfo:
        """Verify that CodeQL is properly installed, and install it if not found.

        Args:
            force_install: If True, force reinstallation even if CodeQL
                is already installed
        """
        self._logger.debug("Verifying CodeQL installation")

        try:
            # First, try to get the binary path
            binary_path = self._codeql_installer.get_binary_path()

            # Install CodeQL if not found OR if force install is requested
            if not binary_path:
                # CodeQL not found - install it automatically
                self._logger.info("CodeQL not found. Installing automatically...")

                try:
                    # Install CodeQL using the installer
                    binary_path = self._codeql_installer.install(force=False)
                    self._logger.info(
                        f"CodeQL installed successfully at: {binary_path}"
                    )
                except Exception as install_error:
                    return CodeQLInstallationInfo(
                        is_installed=False,
                        error_message=f"Failed to install CodeQL: {str(install_error)}",
                    )
            elif force_install:
                # CodeQL exists but force reinstall requested
                self._logger.info("Force reinstall requested. Reinstalling CodeQL...")

                try:
                    # Force reinstall CodeQL
                    binary_path = self._codeql_installer.install(force=True)
                    self._logger.info(
                        f"CodeQL reinstalled successfully at: {binary_path}"
                    )
                except Exception as install_error:
                    return CodeQLInstallationInfo(
                        is_installed=False,
                        error_message=(
                            f"Failed to reinstall CodeQL: {str(install_error)}"
                        ),
                    )

            # Try to get version information to verify installation
            runner = CodeQLRunner(str(binary_path))
            version_result = runner.version()

            if not version_result.success:
                return CodeQLInstallationInfo(
                    is_installed=False,
                    error_message=(
                        f"Failed to get CodeQL version: {version_result.stderr}"
                    ),
                )

            # Parse version from output
            try:
                version_data = json.loads(version_result.stdout)
                version = version_data.get("version", "unknown")
            except (json.JSONDecodeError, KeyError):
                version = "unknown"

            self._logger.info(f"CodeQL version {version} found at {binary_path}")

            return CodeQLInstallationInfo(
                is_installed=True, version=version, path=Path(binary_path)
            )

        except Exception as e:
            return CodeQLInstallationInfo(
                is_installed=False,
                error_message=f"CodeQL verification failed: {str(e)}",
            )

    def _detect_projects(self, repository_path: Path) -> List[ProjectInfo]:
        """Detect projects in the repository."""
        self._logger.debug(f"Detecting projects in: {repository_path}")

        # Convert language detector results to our domain entities
        detected_languages = set()

        # Detect both compiled and non-compiled languages
        all_languages = self._language_detector.detect_all_languages(repository_path)

        # Map detected languages to CodeQL languages
        language_mapping = {
            "javascript": CodeQLLanguage.JAVASCRIPT,
            "typescript": CodeQLLanguage.TYPESCRIPT,
            "python": CodeQLLanguage.PYTHON,
            "java": CodeQLLanguage.JAVA,
            "csharp": CodeQLLanguage.CSHARP,
            "cpp": CodeQLLanguage.CPP,
            "go": CodeQLLanguage.GO,
            "ruby": CodeQLLanguage.RUBY,
            "swift": CodeQLLanguage.SWIFT,
            "actions": CodeQLLanguage.ACTIONS,
        }

        for lang_list in all_languages.values():
            for lang in lang_list:
                if lang in language_mapping:
                    detected_languages.add(language_mapping[lang])

        if not detected_languages:
            self._logger.warning("No supported languages detected in repository")
            return []

        # For now, treat the entire repository as one project
        # In the future, this could be enhanced to detect sub-projects in monorepos
        project_name = repository_path.name or repository_path.resolve().name
        project = ProjectInfo(
            path=repository_path,
            name=project_name,
            languages=detected_languages,
            primary_language=self._determine_primary_language(detected_languages),
        )

        self._logger.info(
            f"Detected project '{project.name}' with languages: "
            f"{[lang.value for lang in detected_languages]}"
        )

        return [project]

    def _filter_projects_by_language(
        self,
        projects: List[ProjectInfo],
        target_languages: Optional[Set[CodeQLLanguage]],
    ) -> List[ProjectInfo]:
        """Filter projects by target languages if specified."""
        if not target_languages:
            return projects

        filtered_projects = []
        for project in projects:
            # Check if project has any of the target languages
            if project.languages.intersection(target_languages):
                filtered_projects.append(project)
            else:
                self._logger.debug(
                    f"Skipping project '{project.name}' - no target languages found"
                )

        return filtered_projects

    def _analyze_project(
        self, project: ProjectInfo, request: CodeQLAnalysisRequest
    ) -> CodeQLAnalysisResult:
        """Analyze a single project with CodeQL."""
        self._logger.info(f"Analyzing project: {project.name}")

        start_time = datetime.now()
        result = CodeQLAnalysisResult(
            project_info=project, status=AnalysisStatus.RUNNING, start_time=start_time
        )

        try:
            # Export CodeQL suites path for this analysis
            self._export_codeql_suites_path()

            # Create output directory
            if request.output_directory:
                output_dir = request.output_directory / project.name
            else:
                output_dir = project.path / "codeql-results"

            output_dir.mkdir(parents=True, exist_ok=True)

            # Analyze each language in the project
            for language in project.languages:
                self._logger.debug(f"Running CodeQL analysis for {language.value}")

                # Create database
                db_path = output_dir / f"db-{language.value}"
                if self._codeql_runner is None:
                    raise Exception("CodeQL runner not initialized")

                db_result = self._codeql_runner.create_database(
                    database_path=str(db_path),
                    source_root=str(project.path),
                    language=language.value,
                    overwrite=True,
                )

                if not db_result.success:
                    error_msg = (
                        f"Failed to create database for {language.value}: "
                        f"{db_result.stderr}"
                    )
                    self._logger.error(error_msg)
                    result.status = AnalysisStatus.FAILED
                    result.error_message = error_msg
                    result.end_time = datetime.now()
                    return result

                # Run analysis
                output_format = "sarif-latest"  # Default output format

                # Map output formats to conventional file extensions
                format_to_extension = {
                    "sarif": ".sarif",
                    "sarif-latest": ".sarif",
                    "csv": ".csv",
                    "json": ".json",
                    "sarifv1": ".sarif",
                    "sarifv2": ".sarif",
                    "text": ".txt",
                }

                file_extension = format_to_extension.get(output_format, ".sarif")
                output_file = output_dir / f"results-{language.value}{file_extension}"
                analysis_result = self._codeql_runner.analyze_database(
                    database_path=str(db_path),
                    output_format=output_format,
                    output=str(output_file),
                )

                if not analysis_result.success:
                    error_msg = (
                        f"Failed to analyze {language.value}: {analysis_result.stderr}"
                    )
                    self._logger.error(error_msg)
                    result.status = AnalysisStatus.FAILED
                    result.error_message = error_msg
                    result.end_time = datetime.now()
                    return result

                # Add output file to results
                if result.output_files is None:
                    result.output_files = []
                result.output_files.append(output_file)

                # Count findings (basic implementation)
                try:
                    if output_format.startswith("sarif"):
                        findings = self._count_sarif_findings(output_file)
                    else:
                        findings = 0  # Placeholder for other formats
                    result.findings_count += findings
                except Exception as e:
                    self._logger.warning(f"Failed to count findings: {e}")

            # Mark as completed
            result.status = AnalysisStatus.COMPLETED
            result.end_time = datetime.now()

            self._logger.info(
                f"Project analysis completed: {project.name} "
                f"(Duration: {result.duration:.2f}s, Findings: {result.findings_count})"
            )

            return result

        except Exception as e:
            error_msg = f"Analysis failed for project {project.name}: {str(e)}"
            self._logger.error(error_msg)

            result.status = AnalysisStatus.FAILED
            result.error_message = error_msg
            result.end_time = datetime.now()

            return result

    def _determine_primary_language(
        self, languages: Set[CodeQLLanguage]
    ) -> Optional[CodeQLLanguage]:
        """Determine the primary language from a set of languages."""
        if not languages:
            return None

        # Priority order for determining primary language
        priority_order = [
            CodeQLLanguage.TYPESCRIPT,
            CodeQLLanguage.JAVASCRIPT,
            CodeQLLanguage.PYTHON,
            CodeQLLanguage.JAVA,
            CodeQLLanguage.CSHARP,
            CodeQLLanguage.GO,
            CodeQLLanguage.CPP,
            CodeQLLanguage.SWIFT,
            CodeQLLanguage.RUBY,
            CodeQLLanguage.ACTIONS,
        ]

        for lang in priority_order:
            if lang in languages:
                return lang

        return next(iter(languages))

    def _count_sarif_findings(self, sarif_file: Path) -> int:
        """Count findings in a SARIF file."""
        try:
            import json

            with open(sarif_file, "r") as f:
                sarif_data = json.load(f)

            total_findings = 0
            for run in sarif_data.get("runs", []):
                results = run.get("results", [])
                total_findings += len(results)

            return total_findings
        except Exception:
            return 0

    def _export_codeql_suites_path(self) -> None:
        """Export CodeQL suites path environment variables."""
        import os

        # Get the CodeQL installation directory
        if self._codeql_runner is None:
            raise Exception("CodeQL runner not initialized")

        codeql_binary_path = Path(self._codeql_runner.codeql_path)
        codeql_root = codeql_binary_path.parent  # This should be the codeql/ directory

        # Set up CodeQL distribution path
        os.environ["CODEQL_DIST"] = str(codeql_root)
        self._logger.debug(f"Set CODEQL_DIST to: {codeql_root}")

        # Set up CodeQL search path for query suites and libraries
        # This includes the qlpacks directory and language-specific directories
        search_paths = []

        # Add qlpacks directory
        qlpacks_path = codeql_root / "qlpacks"
        if qlpacks_path.exists():
            search_paths.append(str(qlpacks_path))

        # Add language-specific directories that contain query suites
        language_dirs = [
            "javascript",
            "python",
            "java",
            "csharp",
            "cpp",
            "go",
            "ruby",
            "swift",
        ]
        for lang_dir in language_dirs:
            lang_path = codeql_root / lang_dir
            if lang_path.exists():
                search_paths.append(str(lang_path))

        if search_paths:
            # Set the search path for CodeQL to find query suites and libraries
            # Use the standard PATH separator for the platform
            path_separator = ":" if os.name != "nt" else ";"
            os.environ["CODEQL_REPO"] = path_separator.join(search_paths)
            self._logger.debug(
                f"Set CODEQL_REPO to: {path_separator.join(search_paths)}"
            )
        else:
            self._logger.warning(
                "Could not find CodeQL qlpacks or language directories"
            )
