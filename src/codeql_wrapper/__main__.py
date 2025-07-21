"""Main entry point for running codeql_wrapper as a module."""

from .entrypoints.cli import cli

if __name__ == "__main__":
    cli()
