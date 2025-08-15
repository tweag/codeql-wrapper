"""CLI command for detecting projects in a repository."""

import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Optional

import click

from codeql_wrapper_v2.application.features.detect_projects.use_cases.detect_projects_use_case import DetectProjectsUseCase
from codeql_wrapper_v2.domain.entities.detect_projects_request import DetectProjectsRequest
from codeql_wrapper_v2.domain.enumerators.language import Language
from codeql_wrapper_v2.domain.exceptions.validation_exceptions import ValidationError
from codeql_wrapper_v2.infrastructure.file_system.file_system_analyzer import FileSystemAnalyzerImpl
from codeql_wrapper_v2.infrastructure.file_system.configuration_reader import JsonConfigurationReader
from codeql_wrapper_v2.infrastructure.services.language_detector import LanguageDetectorImpl
from codeql_wrapper_v2.infrastructure.services.project_detector import ProjectDetectorImpl
from ..dto.cli_input import DetectProjectsCommand
from codeql_wrapper_v2.presentation.dto.cli_output import DetectionOutput, OutputStatus
from codeql_wrapper_v2.presentation.formatters.output_renderer import OutputRenderer

@click.command(name="detect-projects")
@click.argument('repository_path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--monorepo', is_flag=True, help='Treat as monorepo and detect multiple projects')
@click.option('--languages', help='Comma-separated list of target languages (e.g., python,javascript)')
@click.option('--changed-files-only', is_flag=True, help='Only detect projects with changed files')
@click.option('--base-ref', help='Base Git reference for change detection (e.g., main, HEAD~1, commit-hash)')
@click.option('--ref', help='Target Git reference for change detection (e.g., HEAD, branch-name, commit-hash)')
@click.option('--config', type=click.Path(exists=True, dir_okay=False), help='Path to configuration file')
@click.option('--format', 'output_format', type=click.Choice(['json', 'human']), default='human', help='Output format for the results.')
@click.option('--no-colors', is_flag=True, help='Disable colored output in human-readable format.')
@click.option('-q', '--quiet', is_flag=True, help='Suppress non-essential output')
@click.option('-v', '--verbose', is_flag=True, help='Enable verbose logging')
def detect_projects(
    repository_path: str,
    monorepo: bool,
    languages: Optional[str],
    changed_files_only: bool,
    base_ref: Optional[str],
    ref: Optional[str],
    config: Optional[str],
    output_format: str,
    no_colors: bool,
    quiet: bool,
    verbose: bool
) -> None:
    """Detect projects in a repository.
    
    This command analyzes a repository to detect individual projects and their
    programming languages. It supports both single-project repositories and 
    monorepos with multiple projects.
    
    Examples:
        # Basic project detection
        codeql-wrapper detect-projects /path/to/repo
        
        # Detect with specific languages
        codeql-wrapper detect-projects /path/to/repo --languages python,javascript
        
        # Monorepo detection with config file
        codeql-wrapper detect-projects /path/to/repo --monorepo --config projects.json
        
        # JSON output for integration
        codeql-wrapper detect-projects /path/to/repo --format json
    """
    # Create command object
    command = DetectProjectsCommand(
        repository_path=repository_path,
        monorepo=monorepo,
        languages=languages,
        changed_files_only=changed_files_only,
        base_ref=base_ref,
        ref=ref,
        config=config,
        quiet=quiet,
        verbose=verbose
    )
    
    # Set up output renderer
    renderer = OutputRenderer(output_format, use_colors=not no_colors)
    
    # Run installation
    asyncio.run(_run_detection(command, renderer))

async def _run_detection(command: DetectProjectsCommand, renderer: OutputRenderer) -> None:
    """Execute the detection command."""
    try:
        # Configure logging - only if not quiet
        if not command.quiet:
            log_level = logging.DEBUG if command.verbose else logging.INFO
            logging.basicConfig(
                level=log_level,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        logger = logging.getLogger(__name__)
        
        # Show initial message if not quiet
        if not command.quiet:
            renderer.render(DetectionOutput(
                status=OutputStatus.INFO,
                message=f"Starting project detection in: {command.repository_path}"
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
        
        # Convert CLI command to domain request
        request = DetectProjectsRequest(
            repository_path=Path(command.repository_path),
            is_monorepo=command.monorepo,
            target_languages=parsed_languages,
            include_changed_files_only=command.changed_files_only,
            config_file_path=Path(command.config) if command.config else None,
            base_ref=command.base_ref,
            ref=command.ref
        )
        
        # Create dependencies
        file_system_analyzer = FileSystemAnalyzerImpl(logger)
        config_reader = JsonConfigurationReader(logger)
        language_detector = LanguageDetectorImpl(logger)
        project_detector = ProjectDetectorImpl(
            language_detector=language_detector,
            config_reader=config_reader,
            file_system_analyzer=file_system_analyzer,
            logger=logger
        )
        
        # Create use case
        use_case = DetectProjectsUseCase(
            project_detector=project_detector,
            language_detector=language_detector,
            config_reader=config_reader,
            file_system_analyzer=file_system_analyzer,
            logger=logger
        )
        
        # Execute detection
        result = await use_case.execute(request)
        
        # Create output based on result
        if result.is_successful():
            # Convert projects to dictionary format for JSON output
            projects_data = []
            if result.has_projects():
                for project in result.detected_projects:
                    project_data = {
                        "name": project.get_display_name(),
                        "path": str(project.get_relative_path()),
                        "languages": [lang.get_codeql_identifier() for lang in project.detected_languages],
                        "build_mode": project.build_mode,
                    }
                    if project.build_script_path:
                        project_data["build_script_path"] = str(project.build_script_path)
                    if project.queries:
                        project_data["queries"] = project.queries
                    projects_data.append(project_data)
            
            output = DetectionOutput(
                status=OutputStatus.SUCCESS,
                message="Project detection completed successfully!",
                repository_name=result.repository.get_display_name(),
                repository_path=str(result.repository.path),
                is_monorepo=result.is_monorepo,
                project_count=result.get_project_count(),
                config_file_used=result.config_file_used,
                projects=projects_data
            )
        else:
            output = DetectionOutput(
                status=OutputStatus.ERROR,
                message=result.error_message or "Detection failed"
            )
        
        # Render the output
        renderer.render(output)
        
        # Exit with success
        sys.exit(0)
        
    except ValidationError as e:
        output = DetectionOutput(
            status=OutputStatus.ERROR,
            message=f"Validation error: {str(e)}"
        )
        renderer.render(output)
        sys.exit(1)
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Detection failed: {e}")
        error_output = DetectionOutput(
            status=OutputStatus.ERROR,
            message=f"Detection failed: {str(e)}"
        )
        renderer.render(error_output)
        sys.exit(1)


if __name__ == "__main__":
    detect_projects()
