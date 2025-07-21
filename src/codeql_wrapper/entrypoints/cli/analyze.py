"""Analyze command for the CodeQL wrapper CLI."""

import os
from pathlib import Path
from typing import Optional

import click

from ...domain.use_cases.codeql_analysis_use_case import CodeQLAnalysisUseCase
from ...domain.use_cases.sarif_upload_use_case import SarifUploadUseCase
from ...domain.entities.codeql_analysis import (
    CodeQLAnalysisRequest,
    CodeQLLanguage,
    RepositoryAnalysisSummary,
    SarifUploadRequest,
    SarifUploadResult,
)
from ...infrastructure.logger import get_logger
from ...infrastructure.git_utils import GitInfo, GitUtils


@click.command()
@click.argument(
    "repository_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    required=True,
)
@click.option(
    "--languages",
    "-l",
    help="Comma-separated list of languages to analyze (e.g., python,javascript)",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(file_okay=False, dir_okay=True),
    help="Output directory for results",
)
@click.option(
    "--monorepo", is_flag=True, help="Treat as monorepo and analyze sub-projects"
)
@click.option(
    "--force-install",
    is_flag=True,
    help="Force reinstallation of the latest CodeQL even if already installed",
)
@click.option(
    "--upload-sarif",
    is_flag=True,
    help="Upload SARIF results to GitHub Code Scanning after analysis",
)
@click.option(
    "--github-token",
    envvar="GITHUB_TOKEN",
    help="GitHub token for SARIF upload and fetch (or set GITHUB_TOKEN env var)",
)
@click.option(
    "--max-workers",
    type=click.IntRange(1),
    help="Maximum number of worker processes for concurrent analysis "
    "(default: adaptive based on system resources)",
)
@click.option(
    "--only-changed-files",
    is_flag=True,
    help="Only analyze projects that contain changed files (requires Git repository)",
)
@click.option(
    "--base-ref",
    show_default="from env (GITHUB_BASE_REF / CI_MERGE_REQUEST_TARGET_BRANCH_NAME / "
    "BITBUCKET_PR_DESTINATION_BRANCH / main)",
    help="Base Git reference to compare changes from",
)
@click.option(
    "--ref",
    show_default="from env (GITHUB_REF / CI_COMMIT_REF_NAME / BITBUCKET_BRANCH)",
    help="Current git reference (refs/heads/BRANCH-NAME or refs/pull/NUMBER/head or refs/merge/NUMBER/head)",
)
@click.pass_context
def analyze(
    ctx: click.Context,
    repository_path: str,
    languages: Optional[str],
    output_dir: Optional[str],
    monorepo: bool,
    force_install: bool,
    upload_sarif: bool,
    github_token: Optional[str],
    max_workers: Optional[int],
    only_changed_files: bool,
    base_ref: str,
    ref: str,
) -> None:
    """
    Run CodeQL analysis on a repository.

    REPOSITORY_PATH: Path to the repository to analyze
    """

    def _show_upload_sarif_validation(
        git_info: GitInfo, github_token: Optional[str]
    ) -> None:
        if not git_info.repository:
            error_msg = (
                "--repository is required when using --upload-sarif. "
                "Could not auto-detect from Git remote."
            )
            click.echo(
                click.style("ERROR:", fg="red", bold=True) + f" {error_msg}",
                err=True,
            )
            raise click.ClickException(error_msg)

        if not git_info.commit_sha:
            error_msg = (
                "--commit-sha is required when using --upload-sarif. "
                "Could not auto-detect from Git."
            )
            click.echo(
                click.style("ERROR:", fg="red", bold=True) + f" {error_msg}",
                err=True,
            )
            raise click.ClickException(error_msg)

        if not github_token:
            error_msg = (
                "GitHub token is required when using --upload-sarif. "
                "Set GITHUB_TOKEN environment variable or use "
                "--github-token option."
            )
            click.echo(
                click.style("ERROR:", fg="red", bold=True) + f" {error_msg}",
                err=True,
            )
            raise click.ClickException(error_msg)
        else:
            if not os.getenv("GITHUB_TOKEN"):
                os.environ["GITHUB_TOKEN"] = github_token

    def _show_only_changed_files_validation(git_info: GitInfo) -> None:
        if not git_info.is_git_repository:
            error_msg = "--only-changed-files requires a Git repository"
            click.echo(click.style("ERROR:", fg="red", bold=True) + f" {error_msg}")
            raise click.ClickException(error_msg)

        if git_info.base_ref is None:
            error_msg = "No base reference provided. Please use --base-ref option to specify it."
            click.echo(click.style("ERROR:", fg="red", bold=True) + f" {error_msg}")
            raise click.ClickException(error_msg)

        if git_info.current_ref is None:
            error_msg = "It was not possible to determine the current Git reference."
            click.echo(click.style("ERROR:", fg="red", bold=True) + f" {error_msg}")
            raise click.ClickException(error_msg)

    def _parse_languages(languages: Optional[str]) -> set:
        target_languages = set()
        if languages:
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

            for lang in languages.split(","):
                lang = lang.strip().lower()
                if lang in language_mapping:
                    target_languages.add(language_mapping[lang])
                else:
                    logger.warning(f"Unsupported language: {lang}")
        return target_languages

    def _show_validations(max_workers: Optional[int]) -> None:
        # Validate max_workers parameter
        if max_workers is not None:
            if max_workers > 16:
                click.echo(
                    click.style("WARNING:", fg="yellow", bold=True)
                    + f" Using {max_workers} workers may cause resource exhaustion on some systems"
                )

    def _show_success_output(
        summary: RepositoryAnalysisSummary, upload_result: Optional[SarifUploadResult]
    ) -> None:
        click.echo("\n=== CodeQL Analysis Results ===")
        click.echo(f"Repository: {summary.repository_path}")
        click.echo(f"Projects detected: {len(summary.detected_projects)}")
        click.echo(
            f"Analyses completed: {summary.successful_analyses}/"
            f"{len(summary.analysis_results)}"
        )
        click.echo(f"Success rate: {summary.success_rate:.2%}")
        click.echo(f"Total findings: {summary.total_findings}")

        sarif_files = _get_sarif_files(summary)
        click.echo("\nSarif Files:")
        for file in sarif_files:
            click.echo(f"   {file}")

        if summary.failed_analyses > 0:
            click.echo(
                "\n"
                + click.style("WARNING:", fg="yellow", bold=True)
                + f" {summary.failed_analyses} analysis(es) failed"
            )
            for result in summary.analysis_results:
                if not result.is_successful:
                    click.echo(
                        f"  - {result.project_info.name}: {result.error_message}"
                    )

        if upload_result:
            click.echo("\n=== CodeQL Upload Results ===")
            click.echo(f"SARIF files detected: {upload_result.total_files}")
            click.echo(
                f"Uploads completed: {upload_result.successful_uploads}/"
                f"{upload_result.total_files}"
            )
            click.echo(f"Success rate: {upload_result.success_rate:.2%}")

            if upload_result.errors:
                click.echo(
                    "\n" + click.style("ERROR:", fg="red", bold=True) + "Upload Errors:"
                )
                for error in upload_result.errors:
                    click.echo(f"   {error}")
                raise click.ClickException("Failed to upload SARIF files")

    def _show_sarif_files_to_upload(git_info: GitInfo, sarif_files: list) -> None:
        if not sarif_files:
            click.echo(
                "\n"
                + click.style("WARNING:", fg="yellow", bold=True)
                + " No SARIF files found for upload"
            )
        else:
            click.echo(
                "\n"
                + click.style("UPLOADING:", fg="blue", bold=True)
                + f" {len(sarif_files)} SARIF file(s) to {git_info.repository}"
            )
            click.echo(f"   Commit: {git_info.commit_sha}")
            click.echo(f"   Reference: {git_info.current_ref}")

    def _get_sarif_files(summary: RepositoryAnalysisSummary) -> list:
        return [
            output_file
            for result in summary.analysis_results
            if result.output_files
            for output_file in result.output_files
            if output_file.suffix == ".sarif"
        ]

    logger = get_logger(__name__)

    try:
        verbose = ctx.obj.get("verbose", False)
        logger.info(f"Starting CodeQL analysis for: {repository_path}")

        git_utils = GitUtils(Path(repository_path))
        git_info = git_utils.get_git_info(base_ref=base_ref, current_ref=ref)

        _show_validations(max_workers)

        # Validate upload-sarif parameters if upload is requested
        if upload_sarif:
            _show_upload_sarif_validation(git_info, github_token)

        if only_changed_files:
            _show_only_changed_files_validation(git_info)

        # Parse target languages if provided
        target_languages = _parse_languages(languages)

        # Create analysis request
        request = CodeQLAnalysisRequest(
            repository_path=Path(repository_path),
            target_languages=target_languages,
            output_directory=Path(output_dir) if output_dir else None,
            verbose=verbose,
            force_install=force_install,
            monorepo=monorepo,
            max_workers=max_workers,
            only_changed_files=only_changed_files,
            git_info=git_info,
        )

        # Execute analysis
        analysis_use_case = CodeQLAnalysisUseCase(logger)
        summary = analysis_use_case.execute(request)

        # Get sarif files from the analysis results
        sarif_files = _get_sarif_files(summary)

        # Upload SARIF files if requested
        upload_result = None
        if upload_sarif:
            _show_sarif_files_to_upload(git_info, sarif_files)
            if sarif_files:
                # Create upload request
                assert git_info.commit_sha is not None
                assert github_token is not None

                upload_request = SarifUploadRequest(
                    sarif_files=sarif_files,
                    repository=git_info.repository,
                    commit_sha=git_info.commit_sha,
                    github_token=github_token,
                    ref=git_info.current_ref,
                )

                # Execute upload
                upload_use_case = SarifUploadUseCase(logger)
                upload_result = upload_use_case.execute(upload_request)

        _show_success_output(summary, upload_result)
    except click.ClickException:
        # Re-raise ClickException to let Click handle it properly
        raise
    except Exception as e:
        logger.error(f"CodeQL analysis failed: {e}")
        click.echo(click.style("ERROR:", fg="red", bold=True) + f" {e}", err=True)
        raise click.ClickException(str(e))
