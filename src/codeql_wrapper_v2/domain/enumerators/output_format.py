"""Output format enumeration for analysis results."""

from enum import Enum, auto
from typing import Set


class OutputFormat(Enum):
    """Supported output formats for CodeQL analysis results."""
    
    SARIF = auto()
    JSON = auto()
    CSV = auto()
    XML = auto()
    HTML = auto()
    MARKDOWN = auto()
    
    def get_file_extension(self) -> str:
        """Get the file extension for this format."""
        extensions = {
            OutputFormat.SARIF: ".sarif",
            OutputFormat.JSON: ".json",
            OutputFormat.CSV: ".csv",
            OutputFormat.XML: ".xml",
            OutputFormat.HTML: ".html",
            OutputFormat.MARKDOWN: ".md"
        }
        return extensions[self]
    
    def get_codeql_format(self) -> str:
        """Get the CodeQL format for this output format."""
        format_mapping = {
            OutputFormat.SARIF: "sarif",
        }
        return format_mapping[self]
    
    def get_mime_type(self) -> str:
        """Get the MIME type for this format."""
        mime_types = {
            OutputFormat.SARIF: "application/sarif+json",
            OutputFormat.JSON: "application/json",
            OutputFormat.CSV: "text/csv",
            OutputFormat.XML: "application/xml",
            OutputFormat.HTML: "text/html",
            OutputFormat.MARKDOWN: "text/markdown"
        }
        return mime_types[self]
    
    def is_structured(self) -> bool:
        """Check if format supports structured data."""
        return self in {
            OutputFormat.SARIF,
            OutputFormat.JSON,
            OutputFormat.XML
        }
    
    def supports_ci_integration(self) -> bool:
        """Check if format is suitable for CI/CD integration."""
        return self in {
            OutputFormat.SARIF,
            OutputFormat.JSON
        }
    
    @classmethod
    def from_file_extension(cls, extension: str) -> 'OutputFormat':
        """Get format from file extension."""
        extension = extension.lower()
        if not extension.startswith('.'):
            extension = f'.{extension}'
        
        for format_type in cls:
            if format_type.get_file_extension() == extension:
                return format_type
        
        raise ValueError(f"Unsupported file extension: {extension}")