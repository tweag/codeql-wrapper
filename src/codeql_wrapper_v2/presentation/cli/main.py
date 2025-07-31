"""Main CLI entry point for CodeQL wrapper."""

import click

from .codeql_install_command import codeql


@click.group()
@click.version_option(version="0.1.13", prog_name="codeql-wrapper")
def cli():
    """CodeQL Wrapper - Universal CodeQL analysis tool for different project architectures.
    
    This tool provides a universal wrapper for CodeQL analysis across different 
    project architectures (monorepos, single repos) and CI/CD platforms.
    
    Examples:
        # Install CodeQL
        codeql-wrapper codeql install
        
        # Analyze a project
        codeql-wrapper analyze --project-path ./my-project
        
        # Detect projects in repository
        codeql-wrapper project detect --repository-path ./
    """
    pass


# Add command groups
cli.add_command(codeql)
# TODO: Uncomment when these commands are implemented
# cli.add_command(analysis)  
# cli.add_command(project)


if __name__ == "__main__":
    cli()
