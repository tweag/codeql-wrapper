"""SARIF upload use case using CodeQL's built-in functionality."""

import logging
import subprocess
from pathlib import Path
from typing import Optional

from ..entities.codeql_analysis import SarifUploadRequest, SarifUploadResult
from ...infrastructure.codeql_installer import CodeQLInstaller
from ...infrastructure.logger import get_logger


class SarifUploadUseCase:
    """Use case for uploading SARIF files to GitHub Code Scanning using CodeQL CLI."""

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        """
        Initialize the SARIF upload use case.

        Args:
            logger: Logger instance. If None, will create a default logger.
        """
        self._logger = logger or get_logger(__name__)
        self._installer = CodeQLInstaller()

    def execute(self, request: SarifUploadRequest) -> SarifUploadResult:
        """
        Execute SARIF upload to GitHub Code Scanning using CodeQL's built-in command.

        Args:
            request: SARIF upload request containing files and repository info

        Returns:
            SarifUploadResult with upload status and details
        """
        try:
            self._logger.info(
                f"Starting SARIF upload for {request.repository} "
                f"(commit: {request.commit_sha[:8]}...)"
            )

            # Validate CodeQL installation
            self._validate_codeql_installation()

            # Upload files
            successful_uploads = 0
            failed_uploads = 0
            errors = []

            for sarif_file in request.sarif_files:
                try:
                    self._upload_file(sarif_file, request)
                    successful_uploads += 1
                    self._logger.info(f"Successfully uploaded: {sarif_file.name}")
                except Exception as e:
                    failed_uploads += 1
                    error_msg = f"Failed to upload {sarif_file.name}: {e}"
                    errors.append(error_msg)
                    self._logger.error(error_msg)

            # Create result
            success = failed_uploads == 0
            return SarifUploadResult(
                success=success,
                successful_uploads=successful_uploads,
                failed_uploads=failed_uploads,
                total_files=len(request.sarif_files),
                errors=errors if errors else None,
            )

        except Exception as e:
            self._logger.error(f"SARIF upload failed: {e}")
            return SarifUploadResult(
                success=False,
                successful_uploads=0,
                failed_uploads=len(request.sarif_files),
                total_files=len(request.sarif_files),
                errors=[str(e)],
            )

    def _validate_codeql_installation(self) -> None:
        """Validate that CodeQL CLI is installed and accessible."""
        if not self._installer.is_installed():
            raise Exception(
                "CodeQL CLI is not installed. Run 'codeql-wrapper install' first."
            )

    def _upload_file(self, sarif_file: Path, request: SarifUploadRequest) -> None:
        """
        Upload a single SARIF file using CodeQL CLI.

        Args:
            sarif_file: Path to the SARIF file to upload
            request: Upload request with repository and authentication info

        Raises:
            Exception: If upload fails
        """
        # Prepare command
        codeql_path = self._installer.get_binary_path()
        cmd = [
            str(codeql_path),
            "github",
            "upload-results",
            "--sarif",
            str(sarif_file),
            "--repository",
            request.repository,
            "--commit",
            request.commit_sha,
        ]

        # Add ref parameter - use provided ref or default to main branch
        ref = request.ref or "refs/heads/main"
        cmd.extend(["--ref", ref])

        # Add GitHub authentication - pass token via stdin for security
        cmd.append("--github-auth-stdin")

        self._logger.debug(
            f"Uploading {sarif_file} to {request.repository} (ref: {ref})"
        )
        self._logger.debug(
            f"Command: {' '.join(cmd[:-1])} --github-auth-stdin"
        )  # Don't log the actual token

        # Execute command with token passed via stdin
        result = subprocess.run(
            cmd,
            input=request.github_token,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            raise Exception(f"CodeQL upload failed: {error_msg}")

        if result.stdout:
            self._logger.debug(f"CodeQL output: {result.stdout}")
