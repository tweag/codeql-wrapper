
import sys
from codeql_wrapper_v2.presentation.dto.cli_output import CLIOutput, OutputStatus
from codeql_wrapper_v2.presentation.formatters.base_formatter import BaseFormatter
from codeql_wrapper_v2.presentation.formatters.human_formatter import HumanReadableFormatter
from codeql_wrapper_v2.presentation.formatters.json_formatter import JSONFormatter


class OutputRenderer:
    """Main output renderer that handles formatting and display."""
    
    def __init__(self, format_type: str = "human", use_colors: bool = True):
        self.formatter = self._get_formatter(format_type, use_colors)
    
    def _get_formatter(self, format_type: str, use_colors: bool) -> BaseFormatter:
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
