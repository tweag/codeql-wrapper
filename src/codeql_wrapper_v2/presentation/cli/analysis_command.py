"""CLI command for repository analysis."""

import asyncio
import click
import logging
from pathlib import Path
from typing import List, Optional

from codeql_wrapper_v2.application.features.detect_projects.use_cases.detect_projects_use_case import DetectProjectsUseCase
from codeql_wrapper_v2.application.features.install_codeql.use_cases.install_codeql_use_case import InstallCodeQLUseCase
from codeql_wrapper_v2.domain.entities.analyze_repository_request import AnalyzeRepositoryRequest
from codeql_wrapper_v2.domain.entities.detect_projects_request import DetectProjectsRequest
from codeql_wrapper_v2.domain.entities.install_codeql_request import InstallCodeQLRequest
from codeql_wrapper_v2.domain.enumerators.language import Language
from codeql_wrapper_v2.infrastructure.file_system.configuration_reader import JsonConfigurationReader
from codeql_wrapper_v2.infrastructure.file_system.file_system_analyzer import FileSystemAnalyzerImpl
from codeql_wrapper_v2.infrastructure.services.repository_analysis_service import ProjectAnalysisServiceImpl
from codeql_wrapper_v2.infrastructure.services.codeql_service import create_codeql_service
from codeql_wrapper_v2.infrastructure.services.language_detector import LanguageDetectorImpl
from codeql_wrapper_v2.infrastructure.services.project_detector import ProjectDetectorImpl
from codeql_wrapper_v2.presentation.dto.cli_output import AnalyzeOutput, OutputStatus
from codeql_wrapper_v2.presentation.formatters.output_formatter import OutputRenderer

from ...application.features.analyze_repository.use_cases.run_codeql_analysis_use_case import AnalyzeRepositoryUseCase
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

    # Configure logging - only if not quiet
    if not quiet:
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    if not output_directory:
        output_directory = Path.cwd()

    logger = logging.getLogger(__name__)
    
    # Create renderer
    renderer = OutputRenderer(
        format_type=output_format,
        use_colors=not no_colors
    )

    async def run_analysis() -> None:
        try:
            # Show initial message if not quiet
            if not quiet:
                renderer.render(AnalyzeOutput(
                    status=OutputStatus.INFO,
                    message=f"Starting repository analysis in: {repository_path}"
                ))

            # Parse target languages
            parsed_languages: Optional[List[Language]] = None
            if languages:
                lang_strings = [lang.strip() for lang in languages.split(",")]
                parsed_languages = []
                for lang_str in lang_strings:
                    try:
                        lang_enums = Language.from_codeql_identifier(lang_str)
                        parsed_languages.extend(lang_enums)
                    except ValueError:
                        logger.warning(f"Unknown language: {lang_str}")
                        
                # Remove duplicates
                parsed_languages = list(set(parsed_languages)) if parsed_languages else None
            
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
            codeql = create_codeql_service()
            analysis_service = ProjectAnalysisServiceImpl(
                codeql_service=codeql,
                project_detector=project_detector,
                logger=logger
            )            

            # Execute CodeQL installation if needed
            request = InstallCodeQLRequest( )

            install_use_case = InstallCodeQLUseCase(codeql, logger)

            result = await install_use_case.execute(request)

            # Execute project detection
            detect_request = DetectProjectsRequest(
                repository_path=Path(repository_path),
                is_monorepo=monorepo,
                target_languages=parsed_languages,
                include_changed_files_only=changed_files_only,
                config_file_path=Path(config) if config else None,
                base_ref=base_ref,
                ref=ref
            )

            detect_project_use_case = DetectProjectsUseCase(
                project_detector=project_detector,
                language_detector=language_detector,
                config_reader=config_reader,
                file_system_analyzer=file_system_analyzer,
                logger=logger
            )

            detected_projects = await detect_project_use_case.execute(detect_request)

            # Execute analysis
            if not detected_projects.has_projects():
                raise ValueError("No projects detected for analysis")
            
            analyze_request = AnalyzeRepositoryRequest(
                projects=detected_projects.detected_projects,
                output_directory=output_directory
            )

            analyze_use_case = AnalyzeRepositoryUseCase(
                logger=logger,
                analysis_service=analysis_service,
            )

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
                message="Project detection completed successfully!",
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

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            error_output = AnalyzeOutput(
                status=OutputStatus.ERROR,
                message=f"Analysis failed: {e}"
            )
            renderer.render(error_output)
    
    # Run the async operation
    asyncio.run(run_analysis())

if __name__ == "__main__":
    analyze()
