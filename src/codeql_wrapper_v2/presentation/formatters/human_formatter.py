from typing import Any, Dict, List, Optional
from codeql_wrapper_v2.presentation.dto.cli_output import AnalyzeOutput, CLIOutput, DetectionOutput, InstallationOutput, OutputStatus
from codeql_wrapper_v2.presentation.formatters.base_formatter import BaseFormatter


class HumanReadableFormatter(BaseFormatter):
    """Human-readable console output formatter."""
    
    def __init__(self, use_colors: bool = True):
        self.use_colors = use_colors
    
    def format(self, output: CLIOutput) -> str:
        """Format output for human consumption."""
        # Special handling for DetectionOutput
        if isinstance(output, DetectionOutput) and output.status == OutputStatus.SUCCESS:
            return self._format_detection_results(output)

        # Special handling for InstallationOutput
        if isinstance(output, InstallationOutput) and output.status == OutputStatus.SUCCESS:
            return self._format_installation_results(output)
        
        if isinstance(output, AnalyzeOutput):
            return self._format_analyze_results(output)

        # Default formatting for other outputs
        return self._format_default(output)
    
    def _format_default(self, output: CLIOutput) -> str:
        """Default formatting for CLI output."""
       
        # Colors (if enabled)
        if self.use_colors:
            colors = {
                OutputStatus.SUCCESS: "\033[92m",  # Green
                OutputStatus.ERROR: "\033[91m",    # Red
                OutputStatus.WARNING: "\033[93m",  # Yellow
                OutputStatus.INFO: "\033[94m",     # Blue
            }
            reset_color = "\033[0m"
        else:
            colors = {status: "" for status in OutputStatus}
            reset_color = ""
        
        color = colors.get(output.status, "")
        
        formatted = f"{color}{output.message}{reset_color}"
        
        # Add details if present
        if output.details:
            formatted += "\n" + self._format_details(output.details)
            
        return formatted
    
    def _format_details(self, details: Dict[str, Any], indent: int = 0) -> str:
        """Format details dictionary for human reading."""
        lines = []
        indent_str = "  " * indent
        
        for key, value in details.items():
            if isinstance(value, dict):
                lines.append(f"{indent_str}{key}:")
                lines.append(self._format_details(value, indent + 1))
            elif isinstance(value, bool):
                lines.append(f"{indent_str}{key}: {'Yes' if value else 'No'}")
            else:
                lines.append(f"{indent_str}{key}: {value}")
                
        return "\n".join(lines)

    def _format_detection_results(self, output: DetectionOutput) -> str:
        """Format project detection results in a detailed, user-friendly way."""
        lines = []
        
        # Header
        lines.extend(self._get_header("Project Detection Results"))
        
        # Repository info
        lines.extend(self._get_repository_info(
            output.repository_name,
            output.repository_path,
            output.is_monorepo,
            output.config_file_used,
            output.project_count
        ))
        
        # Projects details
        lines.extend(self._get_header("Project Details"))

        if output.projects and len(output.projects) > 0:     
            for project in output.projects:
                lines.extend(self._get_project_info(
                    name=project['name'],
                    path=project['path'],
                    languages=project.get('languages'),
                    build_mode=project.get('build_mode', 'none'),
                    build_script_path=project.get('build_script_path'),
                    queries=project.get('queries'),
                    sarif_files=None
                ))
        else:
            lines.append("No projects detected")
        
        lines.extend(self._get_footer("Detection completed successfully"))
        
        return "\n".join(lines)
    
    def _format_installation_results(self, output: InstallationOutput) -> str:
        """Format installation results in a detailed, user-friendly way."""
        lines = []
        lines.extend(self._get_header("CodeQL Installation Results"))

        lines.append(f"- Status: Success")
        lines.append(f"- Version: {output.version}")
        lines.append(f"- Installation Path: {output.installation_path}")
        lines.append(f"- Is Latest Version: {'Yes' if output.is_latest else 'No'}")
       
        lines.extend(self._get_footer("Installation completed successfully"))
        return "\n".join(lines)

    def _format_analyze_results(self, output: AnalyzeOutput) -> str:
        """Format analyze results in a detailed, user-friendly way."""
        lines = []
        
        # Header
        lines.extend(self._get_header("CodeQL Analysis Results"))
        
        # Repository info
        lines.extend(self._get_repository_info(
            output.repository_name,
            output.repository_path,
            output.is_monorepo,
            output.config_file_used,
            output.project_count
        ))
        
        # Projects details
        if output.successful_projects and len(output.successful_projects) > 0:
            lines.extend(self._get_header("Successful Projects"))
            for project in output.successful_projects:
                lines.extend(self._get_project_info(
                    name=project['name'],
                    path=project['path'],
                    languages=project.get('languages'),
                    build_mode=project.get('build_mode', 'none'),
                    build_script_path=project.get('build_script_path'),
                    queries=project.get('queries'),
                    sarif_files=project.get('sarif_files')
                ))

        if output.failed_projects and len(output.failed_projects) > 0:
            lines.extend(self._get_header("Failed Projects"))

            for project in output.failed_projects:
                lines.extend(self._get_project_info(
                    name=project['name'],
                    path=project['path'],
                    languages=project.get('languages'),
                    build_mode=project.get('build_mode', 'none'),
                    build_script_path=project.get('build_script_path'),
                    queries=project.get('queries'),
                    sarif_files=project.get('sarif_files')
                ))

        lines.extend(self._get_footer("Analysis completed successfully!"))

        return "\n".join(lines)

    def _get_header(self, header:str) -> List[str]:
        """Return the header for the formatter."""
        lines = []

        lines.append("")
        lines.append("=" * 60)
        lines.append(header.upper())
        lines.append("=" * 60)
        lines.append("")

        return lines
    
    def _get_footer(self, footer:str) -> List[str]:
        """Return the footer for the formatter."""
        lines = []

        lines.append("")
        if self.use_colors:
            lines.append(f"\033[92m{footer}!\033[0m")
        else:
            lines.append(f"{footer}")

        return lines
    
    def _get_repository_info(
        self,       
        name: Optional[str] ,
        path: Optional[str] ,
        is_monorepo: Optional[bool],
        config_file: Optional[str] ,
        project_count: Optional[int]
    ) -> List[str]:
        """Return repository information for the formatter."""
        lines = []
        lines.append(f"- Repository: {name}")
        lines.append(f"- Path: {path}")
        repo_type = "- Monorepo" if is_monorepo else "- Single Project"
        lines.append(f"- Type: {repo_type}")
        
        if config_file:
            lines.append(f"- Config: {config_file}")
        if project_count:
            lines.append(f"- Projects Found: {project_count}")

        return lines
    
    def _get_project_info(self, name:Optional[str], path:Optional[str], languages:Optional[List[str]],build_mode:Optional[str], build_script_path:Optional[str], queries:Optional[List[str]], sarif_files: Optional[List[str]] ) -> List[str]:
        """Return project information for the formatter."""
        lines = []
       
        lines.append(f"- {name}")
        lines.append(f"  - Path: {path}")
        
        # Languages
        if languages:
            lang_str = ', '.join(languages)
            lines.append(f"  - Languages: {lang_str}")
        
        # Build info
        if build_mode!= 'none':
            lines.append(f"  - Build Mode: {build_mode}")
        
        if build_script_path:
            lines.append(f"  - Build Script: {build_script_path}")
        
        if queries:
            queries_str = ', '.join(queries)
            lines.append(f"  - Queries: {queries_str}")

        if sarif_files:
            sarif_files_str = ', '.join(sarif_files)
            lines.append(f"  - Sarif files: {sarif_files_str}")

        return lines
    