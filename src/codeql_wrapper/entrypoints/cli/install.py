"""Install command for the CodeQL wrapper CLI."""

import sys

from typing import Optional

import click

from ...infrastructure.logger import get_logger
from ...infrastructure.codeql_installer import CodeQLInstaller


@click.command()
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

    def _show_installation_type(force: bool) -> None:
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

    def _show_success_output(
        current_version: Optional[str],
        installed_version: Optional[str],
        binary_path: str,
    ) -> None:
        if installed_version is None:
            instalation_message = (
                f"CodeQL is already installed (version: {current_version})"
            )
        else:
            instalation_message = f"CodeQL {installed_version} installed successfully!"

        click.echo(
            click.style("SUCCESS:", fg="green", bold=True) + f" {instalation_message}"
        )
        click.echo(f"   Location: {binary_path}")
        click.echo("   Use --force to reinstall CodeQL")

    def _show_error_output(exception: Exception) -> None:
        click.echo(
            click.style("ERROR:", fg="red", bold=True)
            + f" Installation failed: {exception}",
            err=True,
        )
        sys.exit(1)

    logger = get_logger(__name__)

    try:
        logger.info(f"Installing CodeQL version {version}")

        installer = CodeQLInstaller()

        # Check if already installed
        if installer.is_installed() and not force:
            binary_path = installer.get_binary_path() or "Unknown location"
            _show_success_output(installer.get_version(), None, binary_path)
            return

        # Show installation progress
        _show_installation_type(force)

        # Install CodeQL
        binary_path = installer.install(version=version, force=force)

        # Verify installation
        _show_success_output(None, installer.get_version(), binary_path)

    except Exception as e:
        _show_error_output(e)
        sys.exit(1)
