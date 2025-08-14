"""Main CLI entry point for CodeQL wrapper."""

import click

from .codeql_install_command import install
from .detect_projects_command import detect_projects
from .analysis_command import analyze


@click.group()
@click.version_option(version="0.1.13", prog_name="codeql-wrapper")
def cli():
    """CodeQL Wrapper - Universal CodeQL analysis tool for different project architectures.
    
    This tool provides a universal wrapper for CodeQL analysis across different 
    project architectures (monorepos, single repos) and CI/CD platforms.
    
    Examples:
        # Install CodeQL
        codeql-wrapper-v2 codeql install
        
        # Analyze a repository
        codeql-wrapper-v2 analyze --repository-path ./my-project --languages python

        # Detect projects in repository
        codeql-wrapper-v2 detect-projects --repository-path ./
    """
    pass


# Add command groups
cli.add_command(install)
cli.add_command(detect_projects)
cli.add_command(analyze)

if __name__ == "__main__":
    cli()
