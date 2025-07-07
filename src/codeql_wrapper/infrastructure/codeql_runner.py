"""CodeQL runner infrastructure module."""

import subprocess
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

    def __init__(self, codeql_path: Optional[str] = None):
        """
        Initialize CodeQL runner.

        Args:
            codeql_path: Path to CodeQL binary. If None, will try to find it
                automatically.
        """
        self.logger = get_logger(__name__)
        self._codeql_path = codeql_path
        self._installer = CodeQLInstaller()

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

    def _run_command(self, args: List[str], cwd: Optional[str] = None) -> CodeQLResult:
        """
        Run a CodeQL command.

        Args:
            args: Command arguments (without the codeql binary path)
            cwd: Working directory for the command

        Returns:
            CodeQLResult object with command execution details
        """
        command = [self.codeql_path] + args
        self.logger.debug(f"Running command: {' '.join(command)}")

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=300,  # 5 minute timeout
            )

            codeql_result = CodeQLResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                command=command,
            )

            if codeql_result.success:
                self.logger.debug(f"Command succeeded: {' '.join(command)}")
            else:
                self.logger.warning(
                    f"Command failed: {' '.join(command)}, "
                    f"exit code: {result.returncode}"
                )

            return codeql_result

        except subprocess.TimeoutExpired:
            self.logger.error(f"Command timed out: {' '.join(command)}")
            return CodeQLResult(
                success=False,
                stdout="",
                stderr="Command timed out after 5 minutes",
                exit_code=-1,
                command=command,
            )
        except Exception as e:
            self.logger.error(f"Failed to run command: {e}")
            return CodeQLResult(
                success=False, stdout="", stderr=str(e), exit_code=-1, command=command
            )

    def version(self) -> CodeQLResult:
        """
        Get CodeQL version information.

        Returns:
            CodeQLResult with version information
        """
        return self._run_command(["version", "--format=json"])

    def resolve_languages(self, source_root: str) -> CodeQLResult:
        """
        Resolve languages in a source code directory.

        Args:
            source_root: Path to the source code directory

        Returns:
            CodeQLResult with language resolution information
        """
        return self._run_command(["resolve", "languages", "--source-root", source_root])

    def create_database(
        self,
        database_path: str,
        source_root: str,
        language: str,
        command: Optional[str] = None,
        overwrite: bool = False,
    ) -> CodeQLResult:
        """
        Create a CodeQL database.

        Args:
            database_path: Path where the database will be created
            source_root: Path to the source code
            language: Programming language to analyze
            command: Build command (required for compiled languages)
            overwrite: Whether to overwrite existing database

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

        if command:
            args.extend(["--command", command])

        if overwrite:
            args.append("--overwrite")

        return self._run_command(args)

    def analyze_database(
        self,
        database_path: str,
        output_format: str = "sarif-latest",
        output: Optional[str] = None,
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

        args = [
            "database",
            "analyze",
            database_path,
            f"--format={output_format}",
        ]

        if output:
            args.extend(["--output", output])

        return self._run_command(args)

    def run_query(
        self,
        database_path: str,
        query_path: str,
        output_format: str = "table",
        output: Optional[str] = None,
    ) -> CodeQLResult:
        """
        Run a specific query against a database.

        Args:
            database_path: Path to the CodeQL database
            query_path: Path to the query file (.ql)
            output_format: Output format ('table', 'csv', 'json')
            output: Output file path

        Returns:
            CodeQLResult with query execution information
        """
        args = [
            "query",
            "run",
            query_path,
            "--database",
            database_path,
            f"--format={output_format}",
        ]

        if output:
            args.extend(["--output", output])

        return self._run_command(args)

    def pack_download(
        self, pack_name: str, target_dir: Optional[str] = None
    ) -> CodeQLResult:
        """
        Download a CodeQL pack.

        Args:
            pack_name: Name of the pack to download
            target_dir: Directory to download the pack to

        Returns:
            CodeQLResult with download information
        """
        args = ["pack", "download", pack_name]

        if target_dir:
            args.extend(["--dir", target_dir])

        return self._run_command(args)

    def database_finalize(self, database_path: str) -> CodeQLResult:
        """
        Finalize a CodeQL database.

        Args:
            database_path: Path to the database to finalize

        Returns:
            CodeQLResult with finalization information
        """
        return self._run_command(["database", "finalize", database_path])

    def database_cleanup(self, database_path: str) -> CodeQLResult:
        """
        Clean up a CodeQL database.

        Args:
            database_path: Path to the database to clean up

        Returns:
            CodeQLResult with cleanup information
        """
        return self._run_command(["database", "cleanup", database_path])

    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported languages.

        Returns:
            List of supported language names
        """
        result = self.resolve_languages(".")
        if not result.success:
            self.logger.warning("Failed to get supported languages")
            return []

        try:
            # Parse the output to extract languages
            # This is a simplified approach - actual parsing may need refinement
            languages = []
            for line in result.stdout.split("\n"):
                if "language:" in line:
                    lang = line.split("language:")[1].strip()
                    languages.append(lang)
            return languages
        except Exception as e:
            self.logger.error(f"Failed to parse supported languages: {e}")
            return []

    def create_and_analyze(
        self,
        source_root: str,
        language: str,
        output_file: str,
        database_name: Optional[str] = None,
        build_command: Optional[str] = None,
        cleanup_database: bool = True,
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

            # Create database
            create_result = self.create_database(
                str(database_path), source_root, language, build_command, overwrite=True
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
                import shutil

                shutil.rmtree(database_path, ignore_errors=True)
