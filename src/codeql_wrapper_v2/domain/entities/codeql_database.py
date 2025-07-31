from dataclasses import dataclass
from pathlib import Path

from ..enumerators.language import Language

@dataclass(frozen=True)
class CodeQLDatabase:
    """Represents a CodeQL database with metadata."""
    
    path: str
    language: Language
    source_location: str
    
    def get_relative_path(self, base_path: str) -> str:
        """Get database path relative to base directory."""
        try:
            return str(Path(self.path).relative_to(Path(base_path)))
        except ValueError:
            return self.path