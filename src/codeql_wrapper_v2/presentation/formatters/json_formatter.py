
import json
from codeql_wrapper_v2.presentation.dto.cli_output import CLIOutput
from codeql_wrapper_v2.presentation.formatters.base_formatter import BaseFormatter


class JSONFormatter(BaseFormatter):
    """JSON output formatter."""
    
    def format(self, output: CLIOutput) -> str:
        """Format output as JSON."""
        return json.dumps(output.to_dict(), indent=2)