"""CodeQL installation CLI command."""

import asyncio
import logging
import os
import sys
from typing import Optional

import click

from ...infrastructure.services.codeql_service import create_codeql_service
from ...application.features.install_codeql.commands.install_codeql_command import InstallCodeQLCommand
from ...application.features.install_codeql.use_cases.install_codeql_use_case import InstallCodeQLUseCase
from ...domain.constants.codeql_constants import CodeQLConstants
from ...domain.exceptions.codeql_exceptions import (
    CodeQLError,
    CodeQLInstallationError
)
from ..dto.cli_input_dto import InstallCommand
from ..dto.cli_output import (
    InstallationOutput,
    OutputStatus
)
from ..formatters.output_formatter import OutputRenderer


@click.group()
def codeql():
    """CodeQL CLI management commands."""
    pass


@codeql.command()
@click.option(
    "--version", 
    "-v",
    help="Specific CodeQL version to install (e.g., '2.22.0'). If not provided, installs latest version."
)
@click.option(
    "--force", 
    "-f",
    is_flag=True,
    help="Force reinstallation even if the version is already installed."
)
@click.option(
    "--installation-dir",
    "-d",
    help="Custom installation directory. If not provided, uses system default."
)
@click.option(
    "--github-token",
    "-t",
    envvar="GITHUB_TOKEN",
    help="GitHub token for API access (can also use GITHUB_TOKEN env var)."
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["human", "json"]),
    default="human",
    help="Output format."
)
@click.option(
    "--no-colors",
    is_flag=True,
    help="Disable colored output."
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="Suppress non-essential output."
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable verbose output."
)
@click.option(
    "--no-persistent-path",
    is_flag=True,
    help="Don't make PATH changes persistent across sessions."
)
def install(
    version: Optional[str],
    force: bool,
    installation_dir: Optional[str],
    github_token: Optional[str],
    output_format: str,
    no_colors: bool,
    quiet: bool,
    verbose: bool,
    no_persistent_path: bool
) -> None:
    """Install CodeQL CLI.
    
    This command downloads and installs the CodeQL CLI bundle from GitHub releases.
    By default, it installs the latest version unless a specific version is specified.
    
    Examples:
        # Install latest version
        codeql-wrapper codeql install
        
        # Install specific version
        codeql-wrapper codeql install --version 2.22.0
        
        # Force reinstall with custom directory
        codeql-wrapper codeql install --force --installation-dir /opt/codeql
        
        # Install with GitHub token for higher rate limits
        codeql-wrapper codeql install --github-token ghp_xxxxx
    """
    # Create command object
    command = InstallCommand(
        version=version,
        force_reinstall=force,
        installation_directory=installation_dir,
        github_token=github_token,
        persistent_path=not no_persistent_path,
        quiet=quiet,
        verbose=verbose
    )
    
    # Set up output renderer
    renderer = OutputRenderer(output_format, use_colors=not no_colors)
    
    # Run installation
    asyncio.run(_run_install(command, renderer))


async def _run_install(command: InstallCommand, renderer: OutputRenderer) -> None:
    """Execute the installation command."""
    try:
        # Create service with configuration
        service = create_codeql_service(
            installation_directory=command.installation_directory,
            github_token=command.github_token
        )
        
        # Create logger
        logger = logging.getLogger(__name__)
        
        # Create use case
        use_case = InstallCodeQLUseCase(service, logger)
        
        # Convert CLI command to application command
        app_command = InstallCodeQLCommand(
            version=command.version,
            force_reinstall=command.force_reinstall,
            installation_directory=command.installation_directory,
            github_token=command.github_token,
            persistent_path=command.persistent_path,
            quiet=command.quiet,
            verbose=command.verbose
        )
        
        if not command.quiet:
            if command.version:
                msg = f"Installing CodeQL version {command.version}..."
            else:
                msg = "Installing latest CodeQL version..."
            
            if command.force_reinstall:
                msg += " (forced reinstall)"
                
            renderer.render(InstallationOutput(
                status=OutputStatus.INFO,
                message=msg
            ))
        
        # Execute installation using the use case
        result = await use_case.execute(app_command)
        
        # Create success output
        output = InstallationOutput(
            status=OutputStatus.SUCCESS,
            message="CodeQL installation completed successfully!",
            version=result.version,
            installation_path=result.installation_path,
            is_latest=result.is_latest_version,
            available_latest=result.available_latest_version
        )
        
        renderer.render(output)
        
        # Exit with success
        sys.exit(0)
        
    except CodeQLInstallationError as e:
        output = InstallationOutput(
            status=OutputStatus.ERROR,
            message=f"Installation failed: {e.message}",
            details={"installation_path": getattr(e, 'installation_path', 'unknown')}
        )
        renderer.render(output)
        sys.exit(1)
        
    except CodeQLError as e:
        output = InstallationOutput(
            status=OutputStatus.ERROR,
            message=f"CodeQL error: {e.message}"
        )
        renderer.render(output)
        sys.exit(1)
        
    except Exception as e:
        output = InstallationOutput(
            status=OutputStatus.ERROR,
            message=f"Unexpected error: {str(e)}"
        )
        renderer.render(output)
        sys.exit(1)


if __name__ == "__main__":
    codeql()
