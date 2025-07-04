"""Command Line Interface for the hello world application."""

import sys

from typing import Optional

import click

from .domain.use_cases import HelloWorldUseCase
from .infrastructure.logger import configure_logging, get_logger


@click.command()
@click.argument("use_case", required=False)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.version_option(version="0.1.0", prog_name="codeql-wrapper")
def cli(use_case: Optional[str] = None, verbose: bool = False) -> None:
    """
    A clean Python CLI application for CodeQL wrapper functionality.

    This application demonstrates clean code principles with proper
    separation of concerns, dependency injection, and comprehensive logging.

    USE_CASE: The use case to execute (e.g., hello-world)
    """
    # If no use case provided, show help
    if not use_case:
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        ctx.exit()

    try:
        # Configure logging
        configure_logging(verbose=verbose)

        # Get logger
        logger = get_logger(__name__)

        logger.debug("Starting CodeQL wrapper CLI application")
        logger.debug(f"Arguments: use_case={use_case}, verbose={verbose}")

        # Execute based on use case
        if use_case == "hello-world":
            # Create and execute hello world use case
            hello_use_case = HelloWorldUseCase(logger)
            response = hello_use_case.execute("World")

            # Output the result
            click.echo(response.message)
        else:
            click.echo(f"Error: Unknown use case '{use_case}'", err=True)
            click.echo("Available use cases: hello-world", err=True)
            sys.exit(1)

        logger.debug("CodeQL wrapper CLI application completed successfully")

    except ValueError as e:
        logger = get_logger(__name__)
        logger.error(f"Invalid input: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"Unexpected error: {e}")
        click.echo(f"An unexpected error occurred: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
