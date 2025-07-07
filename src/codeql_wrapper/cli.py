"""Command Line Interface for the CodeQL wrapper application."""

import sys
from pathlib import Path
from typing import Optional

import click

from .domain.use_cases.codeql_analysis_use_case import CodeQLAnalysisUseCase
from .domain.entities.codeql_analysis import CodeQLAnalysisRequest, CodeQLLanguage
from .infrastructure.logger import configure_logging, get_logger


def version_callback(ctx: click.Context, param: click.Parameter, value: bool) -> None:
    """Callback for version option."""
    if not value or ctx.resilient_parsing:
        return
    click.echo("0.1.1")
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
    "repository_path", type=click.Path(exists=True, file_okay=False, dir_okay=True)
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
@click.pass_context
def analyze(
    ctx: click.Context,
    repository_path: str,
    languages: Optional[str],
    output_dir: Optional[str],
    monorepo: bool,
    force_install: bool,
) -> None:
    """
    Run CodeQL analysis on a repository.

    REPOSITORY_PATH: Path to the repository to analyze
    """
    try:
        logger = get_logger(__name__)
        verbose = ctx.obj.get("verbose", False)

        logger.info(f"Starting CodeQL analysis for: {repository_path}")

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

        # Create analysis request
        request = CodeQLAnalysisRequest(
            repository_path=Path(repository_path),
            target_languages=target_languages,
            output_directory=Path(output_dir) if output_dir else None,
            verbose=verbose,
            force_install=force_install,
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
            click.echo(f"\n⚠️  {summary.failed_analyses} analysis(es) failed")
            for result in summary.analysis_results:
                if not result.is_successful:
                    click.echo(
                        f"  - {result.project_info.name}: {result.error_message}"
                    )

        # Show output files
        if any(
            result.output_files
            for result in summary.analysis_results
            if result.output_files
        ):
            click.echo("\n📄 Output files:")
            for result in summary.analysis_results:
                if result.output_files:
                    for output_file in result.output_files:
                        click.echo(f"  - {output_file}")

        logger.info("CodeQL analysis completed successfully")

    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"CodeQL analysis failed: {e}")
        click.echo(f"Error: {e}", err=True)
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
            click.echo(f"✅ CodeQL is already installed (version: {current_version})")
            click.echo(f"   Location: {installer.get_binary_path()}")
            click.echo("   Use --force to reinstall")
            return

        # Show installation progress
        if force:
            click.echo("🔄 Force reinstalling CodeQL...")
        else:
            click.echo("📥 Installing CodeQL...")

        # Install CodeQL
        binary_path = installer.install(version=version, force=force)

        # Verify installation
        installed_version = installer.get_version()
        click.echo(f"✅ CodeQL {installed_version} installed successfully!")
        click.echo(f"   Location: {binary_path}")
        click.echo("   You can now run: codeql-wrapper analyze /path/to/repo")

        logger.info(f"CodeQL installation completed: {binary_path}")

    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"CodeQL installation failed: {e}")
        click.echo(f"❌ Installation failed: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
