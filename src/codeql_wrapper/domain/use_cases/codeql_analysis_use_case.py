"""CodeQL analysis use case implementation."""

import json
from concurrent.futures import ProcessPoolExecutor, as_completed
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
from ...infrastructure.language_detector import LanguageDetector, LanguageType
from ...infrastructure.codeql_installer import CodeQLInstaller
from ...infrastructure.codeql_runner import CodeQLRunner
from ...infrastructure.system_resource_manager import SystemResourceManager
from ...infrastructure.logger import configure_logging, get_logger
from ...infrastructure.git_utils import GitUtils

from ...infrastructure.logger import (
    set_project_context,
    clear_project_context,
    set_log_color,
    clear_log_color,
)


class CodeQLAnalysisUseCase:
    """Use case for running CodeQL analysis on repositories."""

    def __init__(self, logger: Any) -> None:
        """Initialize the use case with dependencies."""
        self._logger = get_logger(__name__)
        self.verbose = False
        self._language_detector = LanguageDetector()
        self._codeql_installer = CodeQLInstaller()
        self._codeql_runner: Optional[CodeQLRunner] = None
        self._system_resource_manager = SystemResourceManager(logger)

        # Calculate optimal workers based on system resources (default)
        self._adaptive_max_workers = (
            self._system_resource_manager.calculate_optimal_workers()
        )
        self._manual_max_workers: Optional[int] = None

    @property
    def max_workers(self) -> int:
        """Get the maximum number of workers for this instance."""
        return (
            self._manual_max_workers
            if self._manual_max_workers is not None
            else self._adaptive_max_workers
        )

    def set_max_workers(self, max_workers: Optional[int]) -> None:
        """Set the maximum number of workers manually."""
        if max_workers is not None:
            if max_workers > 16:
                self._logger.warning(
                    f"Using {max_workers} workers may cause resource exhaustion"
                )
            self._logger.info(f"Using manual max_workers: {max_workers}")
        else:
            self._logger.info(
                f"Using adaptive max_workers: {self._adaptive_max_workers}"
            )

        self._manual_max_workers = max_workers

    def execute(self, request: CodeQLAnalysisRequest) -> RepositoryAnalysisSummary:
        """
        Execute CodeQL analysis on a repo or monorepo.

        Args:
            request: CodeQL analysis request

        Returns:
            RepositoryAnalysisSummary with analysis results

        Raises:
            ValueError: If request is invalid
            Exception: If analysis fails
        """
        try:
            # Set max workers from request if provided
            self.set_max_workers(request.max_workers)
            self.verbose = request.verbose

            # Step 1: Verify CodeQL installation once for all projects
            self._logger.info("Verifying CodeQL installation...")
            installation_info = self._verify_codeql_installation(request.force_install)
            if not installation_info.is_valid:
                raise Exception(
                    f"CodeQL installation error: {installation_info.error_message}"
                )

            # Step 2: Initialize CodeQL runner once for all projects
            self._codeql_runner = CodeQLRunner(str(installation_info.path))
            self._logger.info(
                f"CodeQL runner initialized with version {installation_info.version}"
            )

            # Step 3: Detect projects
            config_data = None
            root_config_path = Path(request.repository_path, ".codeql.json")
            if request.monorepo and root_config_path.exists():
                self._logger.info(
                    "Detected .codeql.json in root. Using current directory as repository path."
                )

                with open(root_config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)

            projects: List[ProjectInfo] = self._detect_projects(
                request.monorepo, config_data, request
            )

            # Step 4: Execute analysis
            all_analysis_results = []
            error_messages = []

            # Process projects in parallel using ProcessPoolExecutor
            # CodeQL installation is already verified at this point, so workers can reuse it
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all projects for processing
                futures = []
                for project in projects:
                    future = executor.submit(
                        self._analyze,
                        project,
                        (
                            request.output_directory
                            if request.output_directory is not None
                            else Path(project.project_path) / "codeql-results"
                        ),
                    )
                    futures.append(future)

                # Collect results as they complete
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        all_analysis_results.append(result)
                        if result.error_message:
                            error_messages.append(result.error_message)
                    except Exception as e:
                        self._logger.exception(f"Processing failed: {e}")
                        error_messages.append(str(e))

            # Compose aggregated error string, if any
            aggregated_error = "\n".join(error_messages) if error_messages else None

            return RepositoryAnalysisSummary(
                repository_path=request.repository_path,
                detected_projects=projects,  # Use the original projects list
                analysis_results=all_analysis_results,
                error=aggregated_error,
            )

        except Exception as e:
            self._logger.error(f"CodeQL analysis failed: {e}")
            raise

    def _analyze(
        self, project: ProjectInfo, output_directory: Path
    ) -> CodeQLAnalysisResult:
        """
        Execute CodeQL analysis on a repository.

        Args:
            request: CodeQL analysis request

        Returns:
            CodeQLAnalysisResult with analysis results

        Raises:
            ValueError: If the request is invalid
            Exception: If CodeQL installation or analysis fails
        """

        configure_logging(
            verbose=self.verbose
        )  # Use verbose to see debug messages in worker

        # Set project context for logging
        if project.target_language is not None:
            set_project_context(f"{project.name}({project.target_language.value})")
        else:
            set_project_context(f"{project.name}")

        # Set log color if available
        if project.log_color:
            set_log_color(project.log_color)

        self._logger.info(f"Analyzing project: {project.name}")
        self._logger.debug(f"Project context set: {str(project.project_path)}")
        self._logger.debug(f"Project compiled language: {project.compiled_languages}")
        self._logger.debug(
            f"Project non-compiled language: {project.non_compiled_languages}"
        )
        self._logger.debug(f"Project target language: {project.target_language}")
        self._logger.debug(f"Project build script: {project.build_script}")
        self._logger.debug(f"Project queries: {project.queries}")
        self._logger.debug(f"Project build mode: {project.build_mode}")

        start_time = datetime.now()
        result = CodeQLAnalysisResult(
            project_info=project, status=AnalysisStatus.RUNNING, start_time=start_time
        )

        try:
            # Export CodeQL suites path for this analysis
            self._export_codeql_suites_path()

            output_directory = Path(output_directory, project.name)
            output_directory.mkdir(parents=True, exist_ok=True)

            # Analyze each language in the project
            for language in project.compiled_languages.union(
                project.non_compiled_languages
            ):
                if project.target_language and language != project.target_language:
                    self._logger.debug(
                        f"Skipping language {language.value} as it is not the target "
                        f"language {project.target_language}"
                    )
                    continue

                if self._codeql_runner is None:
                    # Initialize CodeQL runner in worker process
                    import os

                    codeql_path = os.environ.get("CODEQL_WRAPPER_VERIFIED_PATH")
                    if not codeql_path:
                        raise Exception("CodeQL path not found in environment")

                    from ...infrastructure.codeql_runner import CodeQLRunner

                    self._codeql_runner = CodeQLRunner(codeql_path)
                    self._logger.debug(
                        f"Initialized CodeQL runner in worker process: {codeql_path}"
                    )

                # Default output format
                output_format = "sarif-latest"
                output_file = Path(output_directory, f"results-{language.value}.sarif")

                # Explicitly set build_command to None if build_mode is "none"
                build_command = None
                if project.build_mode != "none" and project.build_script:
                    build_command = str(
                        Path(project.repository_path, project.build_script)
                    )
                    self._logger.debug(f"Using build command: {build_command}")
                else:
                    self._logger.debug(
                        f"No build command used (build_mode={project.build_mode})"
                    )

                # Call CodeQL analysis
                analysis_result = self._codeql_runner.create_and_analyze(
                    source_root=str(project.project_path),
                    language=language.value,
                    output_file=str(output_file),
                    database_name=str(output_directory / f"db-{language.value}"),
                    build_command=build_command,
                    cleanup_database=False,
                    build_mode=project.build_mode,
                    queries=project.queries,
                    project_name=project.name,
                )

                if not analysis_result.success:
                    error_msg = (
                        f"Failed to create database and analyze {language.value}: "
                        f"{analysis_result.stderr}"
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
        finally:
            # Clear project context and log color when done
            clear_project_context()
            clear_log_color()

    def _get_project_color(self, project_index: int) -> str:
        """Get a unique color for a project based on its index."""
        # ANSI color codes for different colors
        colors = [
            "\033[92m",  # Bright Green
            "\033[93m",  # Bright Yellow
            "\033[94m",  # Bright Blue
            "\033[95m",  # Bright Magenta
            "\033[96m",  # Bright Cyan
            "\033[97m",  # Bright White
            "\033[32m",  # Dark Green
            "\033[33m",  # Dark Yellow
            "\033[34m",  # Dark Blue
            "\033[35m",  # Dark Magenta
            "\033[36m",  # Dark Cyan
            "\033[90m",  # Dark Gray
            "\033[37m",  # Light Gray
            "\033[1;32m",  # Bold Green
            "\033[1;33m",  # Bold Yellow
            "\033[1;34m",  # Bold Blue
            "\033[1;35m",  # Bold Magenta
            "\033[1;36m",  # Bold Cyan
            "\033[1;37m",  # Bold White
            "\033[38;5;208m",  # Orange (256-color)
            "\033[38;5;129m",  # Purple (256-color)
            "\033[38;5;39m",  # Light Blue (256-color)
            "\033[38;5;46m",  # Lime Green (256-color)
            "\033[38;5;196m",  # Bright Red (256-color)
            "\033[38;5;202m",  # Orange Red (256-color)
            "\033[38;5;214m",  # Gold (256-color)
            "\033[38;5;51m",  # Turquoise (256-color)
            "\033[38;5;165m",  # Hot Pink (256-color)
            "\033[38;5;99m",  # Violet (256-color)
            "\033[38;5;118m",  # Green Yellow (256-color)
            "\033[38;5;75m",  # Sky Blue (256-color)
            "\033[38;5;220m",  # Yellow (256-color)
            "\033[38;5;197m",  # Deep Pink (256-color)
        ]
        return colors[project_index % len(colors)]

    def _detect_projects(
        self,
        isMonorepo: bool,
        configData: Optional[dict],
        request: CodeQLAnalysisRequest,
    ) -> List[ProjectInfo]:
        """Detect projects in the repository."""
        self._logger.debug(f"Detecting projects in: {request.repository_path}")

        projects: List[ProjectInfo] = []
        git_utils = GitUtils(Path(request.repository_path))
        changed_files = git_utils.get_diff_files(request.git_info)

        # Log changed files if any
        for file in changed_files:
            self._logger.debug(f"Changed file: {file}")

        if isMonorepo:
            if configData:
                projects_config = configData.get("projects", [])
                project_index = 0
                for config_index, project in enumerate(projects_config):
                    project_path = Path(
                        request.git_info.working_dir, project.get("path", "")
                    )

                    # Skip project if filtering by changed files and no changes in this project
                    if (
                        request.only_changed_files
                        and not self._project_has_changed_files(
                            project_path, request.git_info.working_dir, changed_files
                        )
                    ):
                        self._logger.debug(
                            f"Skipping project {project_path} - no changed files"
                        )
                        continue

                    # Detect languages first to check if this is a valid project
                    non_compiled_languages = self._detect_languages(
                        project_path, LanguageType.NON_COMPILED
                    )
                    compiled_languages = self._detect_languages(
                        project_path, LanguageType.COMPILED
                    )

                    # Skip if no supported languages are detected
                    if not non_compiled_languages and not compiled_languages:
                        self._logger.debug(
                            f"Skipping project {project_path.name} - no supported languages detected"
                        )
                        continue

                    projects.append(
                        ProjectInfo(
                            repository_path=request.repository_path,
                            project_path=project_path,
                            build_mode=project.get("build-mode", "none"),
                            build_script=(
                                Path(
                                    request.repository_path, project.get("build-script")
                                ).resolve()
                                if project.get("build-script")
                                else None
                            ),
                            queries=project.get("queries", []),
                            name=project_path.name,
                            non_compiled_languages=non_compiled_languages,
                            compiled_languages=compiled_languages,
                            target_language=(
                                CodeQLLanguage(project.get("language"))
                                if project.get("language")
                                else None
                            ),
                            log_color=self._get_project_color(project_index),
                        )
                    )
                    project_index += 1
            else:
                project_index = 0
                for folder in request.repository_path.iterdir():
                    if folder.is_dir():
                        project_name = folder.name or folder.resolve().name

                        # Skip project if filtering by changed files and no changes in this project
                        if (
                            request.only_changed_files
                            and not self._project_has_changed_files(
                                folder, request.repository_path, changed_files
                            )
                        ):
                            self._logger.debug(
                                f"Skipping project {project_name} - no changed files"
                            )
                            continue

                        # Detect languages first to check if this is a valid project
                        non_compiled_languages = self._detect_languages(
                            folder, LanguageType.NON_COMPILED
                        )
                        compiled_languages = self._detect_languages(
                            folder, LanguageType.COMPILED
                        )

                        # Skip if no supported languages are detected
                        if not non_compiled_languages and not compiled_languages:
                            self._logger.debug(
                                f"Skipping project {project_name} - no supported languages detected"
                            )
                            continue

                        projects.append(
                            ProjectInfo(
                                repository_path=request.repository_path,
                                project_path=folder,
                                build_mode="none",
                                build_script=None,
                                queries=[],
                                name=project_name,
                                non_compiled_languages=non_compiled_languages,
                                compiled_languages=compiled_languages,
                                log_color=self._get_project_color(project_index),
                            )
                        )
                        project_index += 1
        else:
            project_name = (
                request.repository_path.name or request.repository_path.resolve().name
            )

            # Detect languages first
            non_compiled_languages = self._detect_languages(
                request.repository_path, LanguageType.NON_COMPILED
            )
            compiled_languages = self._detect_languages(
                request.repository_path, LanguageType.COMPILED
            )

            if request.only_changed_files:
                self._logger.info(
                    "--only-changed-files will not be used in single project mode, "
                    "all files will be analyzed"
                )

            # Only proceed if languages are detected
            if non_compiled_languages or compiled_languages:
                projects.append(
                    ProjectInfo(
                        repository_path=request.repository_path,
                        project_path=request.repository_path,
                        build_mode="none",
                        build_script=None,
                        queries=[],
                        name=project_name,
                        non_compiled_languages=non_compiled_languages,
                        compiled_languages=compiled_languages,
                        log_color=self._get_project_color(0),
                    )
                )
            else:
                self._logger.debug(
                    f"Skipping single project {project_name} - no supported languages detected"
                )

        if not projects:
            if request.only_changed_files:
                self._logger.warning(
                    "No projects with changed files detected in repository"
                )
            else:
                self._logger.warning("No supported projects detected in repository")
        else:
            if request.only_changed_files:
                self._logger.info(
                    f"Found {len(projects)} project(s) with changed files to analyze"
                )
            else:
                self._logger.info(f"Found {len(projects)} project(s) to analyze")

        return projects

    def _project_has_changed_files(
        self, project_path: Path, repository_root_path: Path, changed_files: List[str]
    ) -> bool:
        """Check if a project contains any of the changed files."""
        if not changed_files:
            return False

        # Resolve both paths to absolute paths to avoid relative path issues
        try:
            relative_project_path = project_path.relative_to(repository_root_path)
            project_prefix = str(relative_project_path)
        except (ValueError, OSError):
            # If we can't resolve the relative path, fall back to string comparison
            project_prefix = str(project_path)
            if project_prefix.startswith(str(repository_root_path)):
                # Remove repository path prefix to get relative path
                project_prefix = project_prefix[
                    len(str(repository_root_path)) :
                ].lstrip("/")
            else:
                # Can't determine relationship, skip this project
                return False

        # Check if any changed file is within this project
        for changed_file in changed_files:
            # Root project matches all files
            if project_prefix == "." or project_prefix == "":
                return True
            # Check if file is within project directory
            if changed_file.startswith(f"{project_prefix}/"):
                return True

        return False

    def _detect_languages(
        self, repository_path: Path, languageType: LanguageType
    ) -> Set[CodeQLLanguage]:
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

        # Define which languages are compiled vs non-compiled
        compiled_languages = {"java", "csharp", "cpp", "swift"}
        non_compiled_languages = {
            "javascript",
            "typescript",
            "python",
            "go",
            "ruby",
            "actions",
        }

        target_language_set = (
            compiled_languages
            if languageType == LanguageType.COMPILED
            else non_compiled_languages
        )

        for lang_list in all_languages.values():
            for lang in lang_list:
                if lang in language_mapping and lang in target_language_set:
                    detected_languages.add(language_mapping[lang])

        return detected_languages

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

            # Set environment variable for worker processes to use
            import os

            os.environ["CODEQL_WRAPPER_VERIFIED_PATH"] = str(binary_path)

            return CodeQLInstallationInfo(
                is_installed=True, version=version, path=Path(binary_path)
            )

        except Exception as e:
            return CodeQLInstallationInfo(
                is_installed=False,
                error_message=f"CodeQL verification failed: {str(e)}",
            )

    def _count_sarif_findings(self, sarif_file: Path) -> int:
        """Count findings in a SARIF file."""
        if not sarif_file.exists():
            self._logger.warning(f"SARIF file does not exist: {sarif_file}")
            return 0

        try:
            with open(sarif_file, "r", encoding="utf-8") as f:
                sarif_data = json.load(f)

            total_findings = 0
            for run in sarif_data.get("runs", []):
                results = run.get("results", [])
                total_findings += len(results)

            return total_findings
        except (json.JSONDecodeError, OSError) as e:
            self._logger.warning(f"Failed to parse SARIF file {sarif_file}: {e}")
            return 0
        except Exception as e:
            self._logger.warning(
                f"Unexpected error reading SARIF file {sarif_file}: {e}"
            )
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
