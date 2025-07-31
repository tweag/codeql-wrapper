"""Output formatters for CLI responses."""

import json
import sys
from typing import Dict, Any
from abc import ABC, abstractmethod

from ..dto.cli_output import CLIOutput, OutputStatus


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
