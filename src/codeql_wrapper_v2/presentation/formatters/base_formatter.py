"""Output formatters for CLI responses."""
from abc import ABC, abstractmethod

from ..dto.cli_output import  CLIOutput

class BaseFormatter(ABC):
    """Abstract base class for output formatters."""
    
    @abstractmethod
    def format(self, output: CLIOutput) -> str:
        """Format the output for display."""
        pass

