"""Command Line Interface for the CodeQL wrapper application."""

import sys
from pathlib import Path
from typing import Optional

import click
import colorama

from .domain.use_cases.codeql_analysis_use_case import CodeQLAnalysisUseCase
from .domain.use_cases.sarif_upload_use_case import SarifUploadUseCase
from .domain.entities.codeql_analysis import (
    CodeQLAnalysisRequest,
    CodeQLLanguage,
    SarifUploadRequest,
)
from .infrastructure.logger import configure_logging, get_logger
from .infrastructure.git_utils import GitUtils
from . import __version__

# Initialize colorama for cross-platform color support
colorama.init()


def version_callback(ctx: click.Context, param: click.Parameter, value: bool) -> None:
    """Callback for version option."""
    if not value or ctx.resilient_parsing:
        return
    click.echo(__version__)
    ctx.exit()


@click.group(invoke_without_command=True)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option(
    "--version",
    "-V",
    is_flag=True,
    expose_value=False,
    is_eager=True,
    callback=version_callback,
    help="Show the version and exit.",
)
@click.pass_context
def cli(ctx: click.Context, verbose: bool = False) -> None:
    """
    A universal Python CLI wrapper for running CodeQL analysis.

    This application can run CodeQL analysis on any type of project including
    monorepos and single repositories across different CI/CD platforms.
    """
    # Ensure that ctx.obj exists and is a dict
    ctx.ensure_object(dict)

    # Configure logging
    configure_logging(verbose=verbose)
    ctx.obj["verbose"] = verbose

    # If no command provided, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
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
    "--repository",
    help="GitHub repository in format 'owner/name' for SARIF upload",
)
@click.option(
    "--commit-sha",
    help="Full SHA of the commit being analyzed for SARIF upload",
)
@click.option(
    "--ref",
    help="Git reference (branch or tag) for SARIF upload (default: 'refs/heads/main')",
)
@click.option(
    "--github-token",
    envvar="GITHUB_TOKEN",
    help="GitHub token for SARIF upload (or set GITHUB_TOKEN env var)",
)
@click.option(
    "--max-workers",
    type=click.IntRange(1),
    help="Maximum number of worker processes for concurrent analysis "
    "(default: adaptive based on system resources)",
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
    repository: Optional[str],
    commit_sha: Optional[str],
    ref: Optional[str],
    github_token: Optional[str],
    max_workers: Optional[int],
) -> None:
    """
    Run CodeQL analysis on a repository.

    REPOSITORY_PATH: Path to the repository to analyze
    """
    try:
        logger = get_logger(__name__)
        verbose = ctx.obj.get("verbose", False)

        # If monorepo mode and .codeql.json exists, default repository_path to current directory
        root_config_path = Path(repository_path) / ".codeql.json"
        if monorepo and root_config_path.exists():
            logger.info(
                "Detected .codeql.json in root. Using current directory as repository path."
            )

        logger.info(f"Starting CodeQL analysis for: {repository_path}")

        # Validate upload-sarif parameters if upload is requested
        if upload_sarif:
            # Try to detect Git information automatically if not provided
            git_info = GitUtils.get_git_info(Path(repository_path))

            # Use provided values or fall back to Git detection
            final_repository = repository or git_info.repository
            final_commit_sha = commit_sha or git_info.commit_sha
            final_ref = ref or git_info.ref

            if not final_repository:
                click.echo(
                    click.style("ERROR:", fg="red", bold=True)
                    + " --repository is required when using --upload-sarif. "
                    "Could not auto-detect from Git remote.",
                    err=True,
                )
                sys.exit(1)

            if not final_commit_sha:
                click.echo(
                    click.style("ERROR:", fg="red", bold=True)
                    + " --commit-sha is required when using --upload-sarif. "
                    "Could not auto-detect from Git.",
                    err=True,
                )
                sys.exit(1)

            if not github_token:
                click.echo(
                    click.style("ERROR:", fg="red", bold=True)
                    + " GitHub token is required when using --upload-sarif. "
                    "Set GITHUB_TOKEN environment variable or use "
                    "--github-token option.",
                    err=True,
                )
                sys.exit(1)

            # Update variables for later use
            repository = final_repository
            commit_sha = final_commit_sha
            ref = final_ref

        # Parse target languages if provided
        target_languages = None
        if languages:
            target_languages = set()
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

        # Validate max_workers parameter
        if max_workers is not None:
            if max_workers > 16:
                click.echo(
                    click.style("WARNING:", fg="yellow", bold=True)
                    + f" Using {max_workers} workers may cause resource exhaustion on some systems"
                )

        # Create analysis request
        request = CodeQLAnalysisRequest(
            repository_path=Path(repository_path),
            target_languages=target_languages,
            output_directory=Path(output_dir) if output_dir else None,
            verbose=verbose,
            force_install=force_install,
            monorepo=monorepo,
            max_workers=max_workers,
        )

        # Execute analysis
        analysis_use_case = CodeQLAnalysisUseCase(logger)
        summary = analysis_use_case.execute(request)

        # Display results
        click.echo("\n=== CodeQL Analysis Results ===")
        click.echo(f"Repository: {summary.repository_path}")
        click.echo(f"Projects detected: {len(summary.detected_projects)}")
        click.echo(
            f"Analyses completed: {summary.successful_analyses}/"
            f"{len(summary.analysis_results)}"
        )
        click.echo(f"Success rate: {summary.success_rate:.2%}")
        click.echo(f"Total findings: {summary.total_findings}")

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

        # Show output files
        sarif_files = []
        if any(
            result.output_files
            for result in summary.analysis_results
            if result.output_files
        ):
            click.echo("\n" + click.style("OUTPUT FILES:", fg="blue", bold=True))
            for result in summary.analysis_results:
                if result.output_files:
                    for output_file in result.output_files:
                        click.echo(f"  - {output_file}")
                        if output_file.suffix == ".sarif":
                            sarif_files.append(output_file)

        # Upload SARIF files if requested
        if upload_sarif:
            if not sarif_files:
                click.echo(
                    "\n"
                    + click.style("WARNING:", fg="yellow", bold=True)
                    + " No SARIF files found for upload"
                )
            else:
                # These are guaranteed to be non-None due to validation above
                assert repository is not None
                assert commit_sha is not None
                assert github_token is not None

                # Show upload info
                used_ref = ref or "refs/heads/main"
                click.echo(
                    "\n"
                    + click.style("UPLOADING:", fg="blue", bold=True)
                    + f" {len(sarif_files)} SARIF file(s) to {repository}"
                )
                click.echo(f"   Commit: {commit_sha}")
                click.echo(f"   Reference: {used_ref}")

                # Create upload request
                upload_request = SarifUploadRequest(
                    sarif_files=sarif_files,
                    repository=repository,
                    commit_sha=commit_sha,
                    github_token=github_token,
                    ref=ref,
                )

                # Execute upload
                upload_use_case = SarifUploadUseCase(logger)
                upload_result = upload_use_case.execute(upload_request)

                # Display results
                if upload_result.success:
                    click.echo(
                        "\n"
                        + click.style("SUCCESS:", fg="green", bold=True)
                        + f" Successfully uploaded "
                        f"{upload_result.successful_uploads} SARIF file(s)"
                    )
                else:
                    click.echo(
                        "\n"
                        + click.style("ERROR:", fg="red", bold=True)
                        + f" Upload failed: "
                        f"{upload_result.failed_uploads}/"
                        f"{upload_result.total_files} files failed"
                    )
                    if upload_result.errors:
                        for error in upload_result.errors:
                            click.echo(f"   {error}")
                    sys.exit(1)

        logger.info("CodeQL analysis completed successfully")

    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"CodeQL analysis failed: {e}")
        click.echo(click.style("ERROR:", fg="red", bold=True) + f" {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--version", "-V", default="v2.22.1", help="CodeQL version to install")
@click.option(
    "--force", is_flag=True, help="Force reinstallation even if already installed"
)
@click.pass_context
def install(ctx: click.Context, version: str, force: bool) -> None:
    """
    Install CodeQL CLI.

    This command downloads and installs the CodeQL CLI to ~/.codeql
    """
    try:
        from .infrastructure.codeql_installer import CodeQLInstaller

        logger = get_logger(__name__)
        verbose = ctx.obj.get("verbose", False)  # noqa: F841

        logger.info(f"Installing CodeQL version {version}")

        installer = CodeQLInstaller()

        # Check if already installed
        if installer.is_installed() and not force:
            current_version = installer.get_version()
            click.echo(
                click.style("SUCCESS:", fg="green", bold=True)
                + f" CodeQL is already installed (version: {current_version})"
            )
            click.echo(f"   Location: {installer.get_binary_path()}")
            click.echo("   Use --force to reinstall")
            return

        # Show installation progress
        if force:
            click.echo(
                click.style("REINSTALLING:", fg="yellow", bold=True)
                + " Force reinstalling CodeQL..."
            )
        else:
            click.echo(
                click.style("INSTALLING:", fg="blue", bold=True)
                + " Installing CodeQL..."
            )

        # Install CodeQL
        binary_path = installer.install(version=version, force=force)

        # Verify installation
        installed_version = installer.get_version()
        click.echo(
            click.style("SUCCESS:", fg="green", bold=True)
            + f" CodeQL {installed_version} installed successfully!"
        )
        click.echo(f"   Location: {binary_path}")
        click.echo("   You can now run: codeql-wrapper analyze /path/to/repo")

        logger.info(f"CodeQL installation completed: {binary_path}")

    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"CodeQL installation failed: {e}")
        click.echo(
            click.style("ERROR:", fg="red", bold=True) + f" Installation failed: {e}",
            err=True,
        )
        sys.exit(1)


@cli.command("upload-sarif")
@click.argument(
    "sarif_file", type=click.Path(exists=True, file_okay=True, dir_okay=False)
)
@click.option(
    "--repository",
    "-r",
    help="GitHub repository in format 'owner/name' (auto-detected from Git if not provided)",
)
@click.option(
    "--commit-sha",
    "-c",
    help="Full SHA of the commit that was analyzed (auto-detected from Git if not provided)",
)
@click.option(
    "--ref",
    help="Git reference (branch or tag) that was analyzed (default: 'refs/heads/main')",
)
@click.option(
    "--github-token",
    envvar="GITHUB_TOKEN",
    help="GitHub token for authentication (or set GITHUB_TOKEN env var)",
)
@click.pass_context
def upload_sarif(
    ctx: click.Context,
    sarif_file: str,
    repository: Optional[str],
    commit_sha: Optional[str],
    ref: Optional[str],
    github_token: Optional[str],
) -> None:
    """
    Upload SARIF file to GitHub Code Scanning.

    SARIF_FILE: Path to the SARIF file to upload

    Example:
        codeql-wrapper upload-sarif results.sarif \\
            --repository octocat/Hello-World \\
            --commit-sha a1b2c3d4e5f6 \\
            --ref refs/heads/main
    """
    try:
        logger = get_logger(__name__)

        # Try to detect Git information automatically if not provided
        sarif_file_path = Path(sarif_file)
        # Try to find Git repository by looking at the SARIF file's directory and parents
        git_repo_path = sarif_file_path.parent
        while git_repo_path != git_repo_path.parent:
            if GitUtils.is_git_repository(git_repo_path):
                break
            git_repo_path = git_repo_path.parent
        else:
            # If no Git repo found, use current directory
            git_repo_path = Path.cwd()

        git_info = GitUtils.get_git_info(git_repo_path)

        # Use provided values or fall back to Git detection
        final_repository = repository or git_info.repository
        final_commit_sha = commit_sha or git_info.commit_sha
        final_ref = ref or git_info.ref

        # Debug output (temporary)
        click.echo(
            f"Debug: repository={repository}, git_info.repository={git_info.repository}"
        )
        click.echo(f"Debug: final_repository={final_repository}")

        # Parse repository owner/name
        if not final_repository:
            click.echo(
                click.style("ERROR:", fg="red", bold=True)
                + " Repository is required. Provide --repository or ensure you're in a Git "
                "repository with a GitHub remote configured.",
                err=True,
            )
            sys.exit(1)

        if not final_commit_sha:
            click.echo(
                click.style("ERROR:", fg="red", bold=True)
                + " Commit SHA is required. Provide --commit-sha or ensure you're in a Git "
                "repository.",
                err=True,
            )
            sys.exit(1)

        try:
            repository_owner, repository_name = final_repository.split("/", 1)
        except ValueError:
            click.echo(
                click.style("ERROR:", fg="red", bold=True)
                + " Invalid repository format. Use 'owner/name' format.",
                err=True,
            )
            sys.exit(1)

        # Validate GitHub token
        if not github_token:
            click.echo(
                click.style("ERROR:", fg="red", bold=True)
                + " GitHub token is required. Set GITHUB_TOKEN environment variable "
                "or use --github-token option.",
                err=True,
            )
            sys.exit(1)

        used_ref = final_ref or "refs/heads/main"
        click.echo(
            click.style("UPLOADING:", fg="blue", bold=True)
            + f" SARIF file: {sarif_file}"
        )
        click.echo(f"   Repository: {final_repository}")
        click.echo(f"   Commit: {final_commit_sha}")
        click.echo(f"   Reference: {used_ref}")

        # Show auto-detected information
        if git_info.repository or git_info.commit_sha or git_info.ref:
            auto_detected = []
            if not repository and git_info.repository:
                auto_detected.append("repository")
            if not commit_sha and git_info.commit_sha:
                auto_detected.append("commit-sha")
            if not ref and git_info.ref:
                auto_detected.append("ref")
            if auto_detected:
                click.echo(
                    click.style("INFO:", fg="cyan", bold=True)
                    + f" Auto-detected: {', '.join(auto_detected)}"
                )

        # Create upload request
        upload_request = SarifUploadRequest(
            sarif_files=[Path(sarif_file)],
            repository=final_repository,
            commit_sha=final_commit_sha,
            github_token=github_token,
            ref=final_ref,
        )

        # Execute upload
        upload_use_case = SarifUploadUseCase(logger)
        upload_result = upload_use_case.execute(upload_request)

        # Display results
        if upload_result.success:
            click.echo(
                click.style("SUCCESS:", fg="green", bold=True)
                + " Successfully uploaded SARIF file"
            )
        else:
            if upload_result.errors:
                for error in upload_result.errors:
                    click.echo(click.style("ERROR:", fg="red", bold=True) + f" {error}")
            raise Exception("SARIF upload failed")

        logger.info(f"SARIF upload completed for {final_repository}")

    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"SARIF upload failed: {e}")
        click.echo(
            click.style("ERROR:", fg="red", bold=True) + f" Upload failed: {e}",
            err=True,
        )
        sys.exit(1)
