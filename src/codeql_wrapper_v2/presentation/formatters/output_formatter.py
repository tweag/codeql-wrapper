"""Output formatters for CLI responses."""

import json
import sys
from typing import Dict, Any
from abc import ABC, abstractmethod

from ..dto.cli_output import AnalyzeOutput, CLIOutput, InstallationOutput, OutputStatus, DetectionOutput


class OutputFormatter(ABC):
    """Abstract base class for output formatters."""
    
    @abstractmethod
    def format(self, output: CLIOutput) -> str:
        """Format the output for display."""
        pass


class JSONFormatter(OutputFormatter):
    """JSON output formatter."""
    
    def format(self, output: CLIOutput) -> str:
        """Format output as JSON."""
        return json.dumps(output.to_dict(), indent=2)


class HumanReadableFormatter(OutputFormatter):
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
        # Status indicators
        status_symbols = {
            OutputStatus.SUCCESS: "✅",
            OutputStatus.ERROR: "❌", 
            OutputStatus.WARNING: "⚠️",
            OutputStatus.INFO: "ℹ️"
        }
        
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
        
        symbol = status_symbols.get(output.status, "")
        color = colors.get(output.status, "")
        
        formatted = f"{color}{symbol} {output.message}{reset_color}"
        
        # Add details if present
        if output.details:
            formatted += "\n" + self._format_details(output.details)
            
        return formatted
    
    def _format_detection_results(self, output: DetectionOutput) -> str:
        """Format project detection results in a detailed, user-friendly way."""
        lines = []
        
        # Header
        lines.append("")
        lines.append("=" * 60)
        lines.append("🔍 PROJECT DETECTION RESULTS")
        lines.append("=" * 60)
        lines.append("")
        
        # Repository info
        lines.append(f"📁 Repository: {output.repository_name}")
        lines.append(f"📍 Path: {output.repository_path}")
        repo_type = "Monorepo" if output.is_monorepo else "Single Project"
        lines.append(f"🗂️  Type: {repo_type}")
        
        if output.config_file_used:
            lines.append(f"⚙️  Config: {output.config_file_used}")
        
        lines.append(f"📊 Projects Found: {output.project_count}")
        
        # Projects details
        if output.projects and len(output.projects) > 0:
            lines.append("")
            lines.append("-" * 60)
            lines.append("PROJECT DETAILS")
            lines.append("-" * 60)
            
            for i, project in enumerate(output.projects, 1):
                lines.append(f"\n{i}. {project['name']}")
                lines.append(f"   📍 Path: {project['path']}")
                
                # Languages
                if project.get('languages'):
                    lang_str = ', '.join(project['languages'])
                    lines.append(f"   🔤 Languages: {lang_str}")
                
                # Build info
                if project.get('build_mode', 'none') != 'none':
                    lines.append(f"   🔨 Build Mode: {project['build_mode']}")
                
                if project.get('build_script_path'):
                    lines.append(f"   📜 Build Script: {project['build_script_path']}")
                
                if project.get('queries'):
                    queries_str = ', '.join(project['queries'])
                    lines.append(f"   🔍 Queries: {queries_str}")
        else:
            lines.append("\n❌ No projects detected")
        
        # Footer
        lines.append("\n" + "=" * 60)
        if self.use_colors:
            lines.append("\033[92m✅ Detection completed successfully!\033[0m")
        else:
            lines.append("✅ Detection completed successfully!")
        
        return "\n".join(lines)
    
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

    def _format_installation_results(self, output: InstallationOutput) -> str:
        """Format installation results in a detailed, user-friendly way."""
        lines = []
        lines.append("")
        lines.append("=" * 60)
        lines.append("📦 CODEQL INSTALLATION RESULTS")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"✅ Status: Success")
        lines.append(f"🔢 Version: {output.version}")
        lines.append(f"📍 Installation Path: {output.installation_path}")
        lines.append(f"🆕 Is Latest Version: {'Yes' if output.is_latest else 'No'}")
       
        lines.append("")
        if self.use_colors:
            lines.append("\033[92m✅ CodeQL installed successfully!\033[0m")
        else:
            lines.append("✅ CodeQL installed successfully!")
        return "\n".join(lines)

    def _format_analyze_results(self, output: AnalyzeOutput) -> str:
        """Format analyze results in a detailed, user-friendly way."""
        lines = []
        
        # Header
        lines.append("")
        lines.append("=" * 60)
        lines.append("🔍 PROJECT ANALYSIS RESULTS")
        lines.append("=" * 60)
        lines.append("")
        
        # Repository info
        lines.append(f"📁 Repository: {output.repository_name}")
        lines.append(f"📍 Path: {output.repository_path}")
        repo_type = "Monorepo" if output.is_monorepo else "Single Project"
        lines.append(f"🗂️  Type: {repo_type}")
        
        if output.config_file_used:
            lines.append(f"⚙️  Config: {output.config_file_used}")
        
        lines.append(f"📊 Projects Found: {output.project_count}")
        
        # Projects details
        if output.successful_projects and len(output.successful_projects) > 0:
            lines.append("")
            lines.append("-" * 60)
            lines.append("SUCCESSFUL PROJECT DETAILS")
            lines.append("-" * 60)

            for i, project in enumerate(output.successful_projects, 1):
                lines.append(f"\n{i}. {project['name']}")
                lines.append(f"   📍 Path: {project['path']}")
                
                # Languages
                if project.get('languages'):
                    lang_str = ', '.join(project['languages'])
                    lines.append(f"   🔤 Languages: {lang_str}")
                
                # Build info
                if project.get('build_mode', 'none') != 'none':
                    lines.append(f"   🔨 Build Mode: {project['build_mode']}")
                
                if project.get('build_script_path'):
                    lines.append(f"   📜 Build Script: {project['build_script_path']}")
                
                if project.get('queries'):
                    lines.append(f"   🔍 Queries: {', '.join(project['queries'])}")

                if project.get('sarif_files'):
                    sarif_files = ', '.join(project['sarif_files'])
                    lines.append(f"   📄 SARIF Files: {sarif_files}")

        if output.failed_projects and len(output.failed_projects) > 0:
            lines.append("")
            lines.append("-" * 60)
            lines.append("FAILED PROJECT DETAILS")
            lines.append("-" * 60)

            for i, project in enumerate(output.failed_projects, 1):
                lines.append(f"\n{i}. {project['name']}")
                lines.append(f"   📍 Path: {project['path']}")
                
                # Languages
                if project.get('languages'):
                    lang_str = ', '.join(project['languages'])
                    lines.append(f"   🔤 Languages: {lang_str}")
                
                # Build info
                if project.get('build_mode', 'none') != 'none':
                    lines.append(f"   🔨 Build Mode: {project['build_mode']}")
                
                if project.get('build_script_path'):
                    lines.append(f"   📜 Build Script: {project['build_script_path']}")
                
                if project.get('queries'):
                    lines.append(f"   🔍 Queries: {', '.join(project['queries'])}")

                if project.get('error_message'):
                    lines.append(f"   ❌ Error: {project['error_message']}")

        # Footer
        lines.append("\n" + "=" * 60)
        if self.use_colors:
            lines.append("\033[92m✅ Analysis completed successfully!\033[0m")
        else:
            lines.append("✅ Analysis completed successfully!")

        return "\n".join(lines)

class OutputRenderer:
    """Main output renderer that handles formatting and display."""
    
    def __init__(self, format_type: str = "human", use_colors: bool = True):
        self.formatter = self._get_formatter(format_type, use_colors)
    
    def _get_formatter(self, format_type: str, use_colors: bool) -> OutputFormatter:
        """Get the appropriate formatter."""
        if format_type == "json":
            return JSONFormatter()
        elif format_type == "human":
            return HumanReadableFormatter(use_colors)
        else:
            raise ValueError(f"Unknown format type: {format_type}")
    
    def render(self, output: CLIOutput) -> None:
        """Render output to appropriate stream."""
        formatted = self.formatter.format(output)
        
        # Write to stderr for errors, stdout for everything else
        if output.status == OutputStatus.ERROR:
            print(formatted, file=sys.stderr)
        else:
            print(formatted)
    
    def render_string(self, output: CLIOutput) -> str:
        """Render output as string without printing."""
        return self.formatter.format(output)
