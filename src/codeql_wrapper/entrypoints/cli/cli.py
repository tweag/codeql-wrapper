"""Main CLI entry point for the CodeQL wrapper application."""

import click
import colorama

from ...infrastructure.logger import configure_logging
from ... import __version__

# Import and register commands
from .analyze import analyze
from .install import install

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


cli.add_command(analyze)
cli.add_command(install)
