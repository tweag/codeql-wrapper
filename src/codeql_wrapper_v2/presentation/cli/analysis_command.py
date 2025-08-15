"""CLI command for repository analysis."""

import asyncio
import click
import logging
import sys
from pathlib import Path
from typing import List, Optional

from codeql_wrapper_v2.infrastructure.dependency_injection import get_service_registry
from codeql_wrapper_v2.application.use_cases.detect_projects_use_case import DetectProjectsUseCase
from codeql_wrapper_v2.application.use_cases.install_codeql_use_case import InstallCodeQLUseCase
from codeql_wrapper_v2.application.use_cases.run_codeql_analysis_use_case import AnalyzeRepositoryUseCase
from codeql_wrapper_v2.domain.entities.analyze_repository_request import AnalyzeRepositoryRequest
from codeql_wrapper_v2.domain.entities.detect_projects_request import DetectProjectsRequest
from codeql_wrapper_v2.domain.entities.install_codeql_request import InstallCodeQLRequest
from codeql_wrapper_v2.domain.enumerators.language import Language
from codeql_wrapper_v2.domain.exceptions.validation_exceptions import ValidationError
from ..dto.cli_input import AnalyzeCommand
from codeql_wrapper_v2.presentation.dto.cli_output import AnalyzeOutput, OutputStatus
from codeql_wrapper_v2.presentation.formatters.output_renderer import OutputRenderer

from ...domain.entities.analysis_result import RepositoryAnalysisResult


@click.command(name="analyze")
@click.argument(
    "repository_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path)
)
@click.option('--languages', help='Comma-separated list of target languages (e.g., python,javascript)')
@click.option(
    "--monorepo",
    is_flag=True,
    help="Treat repository as monorepo with multiple projects"
)
@click.option(
    "--changed-files-only",
    is_flag=True,
    help="Only analyze projects with changed files"
)
@click.option(
    "--base-ref",
    type=str,
    help="Base git reference for change detection (e.g., main, HEAD~1)"
)
@click.option(
    "--ref",
    type=str,
    help="Current git reference for change detection (default: HEAD)"
)
@click.option(
    "--config",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    help="Path to CodeQL configuration file"
)
@click.option(
    "--output-directory", "-o",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    help="Directory to save analysis results"
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable verbose logging"
)
@click.option('--no-colors', is_flag=True, help='Disable colored output in human-readable format.')
@click.option('-q', '--quiet', is_flag=True, help='Suppress non-essential output')
@click.option('--format', 'output_format', type=click.Choice(['json', 'human']), default='human', help='Output format for the results.')
def analyze(
    repository_path: Path,
    languages: Optional[str],
    monorepo: bool,
    changed_files_only: bool,
    base_ref: Optional[str],
    ref: Optional[str],
    config: Optional[Path],
    output_directory: Optional[Path],
    verbose: bool,
    quiet: bool,
    no_colors: bool,
    output_format: str
) -> None:
    """Analyze a repository with CodeQL.
    
    This command performs the complete CodeQL analysis workflow:
    1. Validates/installs CodeQL if needed
    2. Detects projects in the repository
    3. Creates CodeQL databases for each project and language
    4. Runs CodeQL analysis queries
    5. Generates SARIF output files
    
    Examples:
        # Analyze Python code in current directory
        codeql-wrapper-v2 analyze --repository-path . --languages python
        
        # Analyze multiple languages in a monorepo
        codeql-wrapper-v2 analyze -r ./my-repo --languages python,javascript --monorepo
        
        # Analyze only changed files since main branch
        codeql-wrapper-v2 analyze -r . --changed-files-only --base-ref main --languages python
    """
    
    # Create command object
    command = AnalyzeCommand(
        repository_path=str(repository_path),
        languages=languages,
        monorepo=monorepo,
        changed_files_only=changed_files_only,
        base_ref=base_ref,
        ref=ref,
        config=str(config) if config else None,
        output_directory=str(output_directory) if output_directory else None,
        verbose=verbose,
        quiet=quiet
    )
    
    # Set up output renderer
    renderer = OutputRenderer(output_format, use_colors=not no_colors)
    
    # Run installation
    asyncio.run(_run_analysis(command, renderer))

async def _run_analysis(command: AnalyzeCommand, renderer: OutputRenderer) -> None:
    """Execute the analysis command."""
    try:
        # Configure logging - only if not quiet
        if not command.quiet:
            log_level = logging.DEBUG if command.verbose else logging.INFO
            logging.basicConfig(
                level=log_level,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

        # Set default output directory
        output_directory = Path(command.output_directory) if command.output_directory else Path.cwd()

        logger = logging.getLogger(__name__)
        
        # Get service registry and configure services
        registry = get_service_registry()
        registry.configure()
        
        # Get the DI container
        container = registry.get_container()
        
        # Show initial message if not quiet
        if not command.quiet:
            renderer.render(AnalyzeOutput(
                status=OutputStatus.INFO,
                message=f"Starting repository analysis in: {command.repository_path}"
            ))

        # Parse target languages
        parsed_languages: Optional[List[Language]] = None
        if command.languages:
            lang_strings = [lang.strip() for lang in command.languages.split(",")]
            parsed_languages = []
            for lang_str in lang_strings:
                try:
                    lang_enums = Language.from_codeql_identifier(lang_str)
                    parsed_languages.extend(lang_enums)
                except ValueError:
                    logger.warning(f"Unknown language: {lang_str}")
                    
            # Remove duplicates
            parsed_languages = list(set(parsed_languages)) if parsed_languages else None

        # Execute CodeQL installation if needed
        request = InstallCodeQLRequest()
        install_use_case = container.get(InstallCodeQLUseCase)
        result = await install_use_case.execute(request)

        # Execute project detection
        detect_request = DetectProjectsRequest(
            repository_path=Path(command.repository_path),
            is_monorepo=command.monorepo,
            target_languages=parsed_languages,
            include_changed_files_only=command.changed_files_only,
            config_file_path=Path(command.config) if command.config else None,
            base_ref=command.base_ref,
            ref=command.ref
        )

        detect_project_use_case = container.get(DetectProjectsUseCase)
        detected_projects = await detect_project_use_case.execute(detect_request)

        # Execute analysis
        if not detected_projects.has_projects():
            raise ValueError("No projects detected for analysis")
        
        analyze_request = AnalyzeRepositoryRequest(
            projects=detected_projects.detected_projects,
            output_directory=output_directory
        )

        analyze_use_case = container.get(AnalyzeRepositoryUseCase)
        result = await analyze_use_case.execute(analyze_request)

        # Convert projects to dictionary format for JSON output
        successful_projects = []
        failed_projects = []

        for analysis in result.successful_projects:
            project_data = {
                "name": analysis.project.get_display_name(),
                "path": str(analysis.project.get_relative_path()),
                "languages": [lang.get_codeql_identifier() for lang in analysis.project.detected_languages],
                "build_mode": analysis.project.build_mode,
                "sarif_files": [str(file) for file in analysis.output_files],
            }
            if analysis.project.build_script_path:
                project_data["build_script_path"] = str(analysis.project.build_script_path)
            if analysis.project.queries:
                project_data["queries"] = analysis.project.queries
            else:
                if analysis.project.target_language:
                    project_data["queries"] = [f"{analysis.project.target_language.get_codeql_identifier()}-code-scanning"]
                else: 
                    project_data["queries"] = []
                    for lang in analysis.project.detected_languages:
                        project_data["queries"].append(f"{lang.get_codeql_identifier()}-code-scanning")
            successful_projects.append(project_data)

        for analysis in result.failed_projects:
            project_data = {
                "name": analysis.project.get_display_name(),
                "path": str(analysis.project.get_relative_path()),
                "languages": [lang.get_codeql_identifier() for lang in analysis.project.detected_languages],
                "build_mode": analysis.project.build_mode,
                "error_message": analysis.error_message,
            }
            if analysis.project.build_script_path:
                project_data["build_script_path"] = str(analysis.project.build_script_path)
            if analysis.project.queries:
                project_data["queries"] = analysis.project.queries
            else:
                if analysis.project.target_language:
                    project_data["queries"] = [f"{analysis.project.target_language.get_codeql_identifier()}-code-scanning"]
                else: 
                    project_data["queries"] = []
                    for lang in analysis.project.detected_languages:
                        project_data["queries"].append(f"{lang.get_codeql_identifier()}-code-scanning")
            failed_projects.append(project_data)

        message = "Analysis completed successfully!" if result.is_successful() else "Analysis completed with errors."

        output = AnalyzeOutput(
            status=OutputStatus.SUCCESS if result.is_successful() else OutputStatus.ERROR,
            message=message,
            repository_name=detected_projects.repository.get_display_name(),
            repository_path=str(detected_projects.repository.path),
            is_monorepo=detected_projects.is_monorepo,
            project_count=detected_projects.get_project_count(),
            config_file_used=detected_projects.config_file_used,
            successful_projects=successful_projects,
            failed_projects=failed_projects
        )
    
        # Render the output
        renderer.render(output)
        
        # Exit with success or error code based on results
        if result.is_successful():
            sys.exit(0)
        else:
            sys.exit(1)

    except ValidationError as e:
        output = AnalyzeOutput(
            status=OutputStatus.ERROR,
            message=f"Validation error: {str(e)}"
        )
        renderer.render(output)
        sys.exit(1)
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Analysis failed: {e}")
        error_output = AnalyzeOutput(
            status=OutputStatus.ERROR,
            message=f"Analysis failed: {str(e)}"
        )
        renderer.render(error_output)
        sys.exit(1)


if __name__ == "__main__":
    analyze()
