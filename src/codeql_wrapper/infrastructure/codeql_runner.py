"""CodeQL runner infrastructure module."""

import subprocess
import os  # Added for chmod
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

from .logger import get_logger
from .codeql_installer import CodeQLInstaller


@dataclass
class CodeQLResult:
    """Result of a CodeQL command execution."""

    success: bool
    stdout: str
    stderr: str
    exit_code: int
    command: List[str]


class CodeQLRunner:
    """Handles running CodeQL commands and analysis."""

    def __init__(self, codeql_path: Optional[str] = None, timeout: int = 300):
        """
        Initialize CodeQL runner.

        Args:
            codeql_path: Path to CodeQL binary. If None, will try to find it
                automatically.
            timeout: Timeout in seconds for CodeQL commands (default: 300)
        """
        self.logger = get_logger(__name__)
        self._codeql_path = codeql_path
        self._installer = CodeQLInstaller()
        self._timeout = timeout

    @property
    def codeql_path(self) -> str:
        """
        Get the path to the CodeQL binary.

        Returns:
            Path to CodeQL binary

        Raises:
            Exception: If CodeQL is not installed and no path provided
        """
        if self._codeql_path:
            return self._codeql_path

        # Try to get from installer
        binary_path = self._installer.get_binary_path()
        if binary_path:
            return binary_path

        raise Exception(
            "CodeQL not found. Please install CodeQL first or provide "
            "the path to the binary."
        )

    def version(self) -> CodeQLResult:
        """
        Get CodeQL version information.

        Returns:
            CodeQLResult with version information
        """
        return self._run_command(["version", "--format=json"])

    def create_database(
        self,
        database_path: str,
        source_root: str,
        language: str,
        command: Optional[str] = None,
        build_mode: Optional[str] = None,
    ) -> CodeQLResult:
        """
        Create a CodeQL database.

        Args:
            database_path: Path where the database will be created
            source_root: Path to the source code
            language: Programming language to analyze
            command: Build command (required for compiled languages)
            build_mode: Build mode for the database creation

        Returns:
            CodeQLResult with database creation information
        """
        args = [
            "database",
            "create",
            database_path,
            "--source-root",
            source_root,
            "--language",
            language,
        ]

        # Only add build-mode if specified and not "none"
        if build_mode:
            args.extend(["--build-mode", build_mode])
        else:
            args.extend(["--build-mode", "none"])

        if command:
            args.extend(["--command", command])

        args.append("--force-overwrite")

        return self._run_command(args)

    def analyze_database(
        self,
        database_path: str,
        output_format: str = "sarif-latest",
        output: Optional[str] = None,
        queries: Optional[List[str]] = None,
    ) -> CodeQLResult:
        """
        Analyze a CodeQL database.

        Args:
            database_path: Path to the CodeQL database
            output_format: Output format ('sarif-latest', 'csv', 'json')
            output: Output file path

        Returns:
            CodeQLResult with analysis information
        """
        # Determine output format based on output file extension if not specified
        if output and output_format == "sarif-latest":
            if output.endswith(".csv"):
                output_format = "csv"
            elif output.endswith(".json"):
                output_format = "json"

        args = ["database", "analyze", database_path, f"--format={output_format}"]

        if output:
            args.extend(["--output", output])

        if queries:
            args.extend(queries)

        return self._run_command(args)

    def create_and_analyze(
        self,
        source_root: str,
        language: str,
        output_file: str,
        database_name: Optional[str] = None,
        build_command: Optional[str] = None,
        cleanup_database: bool = True,
        build_mode: Optional[str] = None,
        queries: Optional[List[str]] = None,
    ) -> CodeQLResult:
        """
        High-level method to create database and run analysis in one step.

        Args:
            source_root: Path to source code
            language: Programming language
            output_file: Path for analysis results
            database_name: Name for the database (defaults to temp directory)
            build_command: Build command for compiled languages
            cleanup_database: Whether to clean up the database after analysis

        Returns:
            CodeQLResult with final analysis information
        """
        import tempfile

        # Create database path
        if not database_name:
            database_path = Path(tempfile.mkdtemp()) / "codeql-database"
        else:
            database_path = Path(database_name)

        try:
            self.logger.info(
                f"Creating CodeQL database for {language} at {database_path}"
            )

            # Ensure build_command script is executable if provided
            if build_command:
                build_script_path = Path(build_command)
                if build_script_path.exists():
                    try:
                        os.chmod(build_script_path, 0o755)  # Make script executable
                        self.logger.debug(
                            f"Set executable permissions for {build_script_path}"
                        )
                    except Exception as e:
                        self.logger.warning(
                            f"Failed to set executable permissions for {build_script_path}: {e}"
                        )
                else:
                    self.logger.error(
                        f"Build script does not exist: {build_script_path}"
                    )
                    return CodeQLResult(
                        success=False,
                        stdout="",
                        stderr=f"Build script does not exist: {build_script_path}",
                        exit_code=-1,
                        command=[],
                    )

            # Create database
            create_result = self.create_database(
                str(database_path),
                source_root,
                language,
                build_command,
                build_mode=build_mode,
            )

            if not create_result.success:
                self.logger.error(f"Database creation failed: {create_result.stderr}")
                return create_result

            self.logger.info("Database created successfully")

            # Analyze database
            self.logger.info("Running analysis on the database")
            analyze_result = self.analyze_database(
                str(database_path),
                output_format="sarif-latest",
                output=output_file,
                queries=queries,
            )

            if not analyze_result.success:
                self.logger.error(f"Analysis failed: {analyze_result.stderr}")
                return analyze_result

            self.logger.info(
                f"Analysis completed successfully. Results saved to {output_file}"
            )
            return analyze_result

        finally:
            # Cleanup database if requested
            if cleanup_database and database_path.exists():
                self.logger.info(f"Cleaning up database at {database_path}")

    # Private methods
    def _run_command(self, args: List[str], cwd: Optional[str] = None) -> CodeQLResult:
        command = [self.codeql_path] + args
        self.logger.debug(f"Running command: {' '.join(command)}")

        if "--command" in args:
            self.logger.debug(f"Build command: {args[args.index('--command') + 1]}")
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=self._timeout,
            )
            codeql_result = CodeQLResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                command=command,
            )
            if not codeql_result.success:
                self.logger.error(
                    f"Command failed with exit code {result.returncode}: {result.stderr}"
                )
            return codeql_result
        except subprocess.TimeoutExpired:
            self.logger.error(
                f"Command timed out after {self._timeout} seconds: {' '.join(command)}"
            )
            return CodeQLResult(
                success=False,
                stdout="",
                stderr=f"Command timed out after {self._timeout} seconds",
                exit_code=-1,
                command=command,
            )
        except Exception as e:
            self.logger.error(f"Failed to run command: {e}")
            return CodeQLResult(
                success=False, stdout="", stderr=str(e), exit_code=-1, command=command
            )
