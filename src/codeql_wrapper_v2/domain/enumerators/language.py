"""Programming language enumeration for CodeQL analysis."""

from enum import Enum, auto
from typing import Set, List


class Language(Enum):
    """Supported programming languages for CodeQL analysis."""
    
    JAVASCRIPT = auto()
    TYPESCRIPT = auto()
    PYTHON = auto()
    JAVA = auto()
    CSHARP = auto()
    CPP = auto()
    C = auto()
    GO = auto()
    RUBY = auto()
    SWIFT = auto()
    KOTLIN = auto()
    RUST = auto()
    
    def get_codeql_identifier(self) -> str:
        """Get the CodeQL identifier for this language."""
        language_mapping = {
            Language.JAVASCRIPT: "javascript",
            Language.TYPESCRIPT: "javascript",  # TypeScript uses JavaScript extractor
            Language.PYTHON: "python",
            Language.JAVA: "java",
            Language.CSHARP: "csharp",
            Language.CPP: "cpp",
            Language.C: "cpp",  # C uses C++ extractor
            Language.GO: "go",
            Language.RUBY: "ruby",
            Language.SWIFT: "swift",
            Language.KOTLIN: "java",  # Kotlin uses Java extractor
            Language.RUST: "rust"
        }
        return language_mapping[self]
    
    def get_file_extensions(self) -> Set[str]:
        """Get common file extensions for this language."""
        extension_mapping = {
            Language.JAVASCRIPT: {".js", ".jsx", ".mjs", ".cjs"},
            Language.TYPESCRIPT: {".ts", ".tsx", ".d.ts"},
            Language.PYTHON: {".py", ".pyw", ".py3", ".pyi"},
            Language.JAVA: {".java"},
            Language.CSHARP: {".cs", ".csx"},
            Language.CPP: {".cpp", ".cxx", ".cc", ".C", ".hpp", ".hxx", ".h++"},
            Language.C: {".c", ".h"},
            Language.GO: {".go"},
            Language.RUBY: {".rb", ".rbw"},
            Language.SWIFT: {".swift"},
            Language.KOTLIN: {".kt", ".kts"},
            Language.RUST: {".rs"}
        }
        return extension_mapping[self]
    
    def is_compiled_language(self) -> bool:
        """Check if this is a compiled language requiring build steps."""
        compiled_languages = {
            Language.JAVA,
            Language.CSHARP,
            Language.CPP,
            Language.C,
            Language.GO,
            Language.SWIFT,
            Language.KOTLIN,
            Language.RUST
        }
        return self in compiled_languages
    
    @classmethod
    def detect_from_extension(cls, file_extension: str) -> List['Language']:
        """Detect possible languages from file extension."""
        extension = file_extension.lower()
        if not extension.startswith('.'):
            extension = f'.{extension}'
        
        detected_languages = []
        for language in cls:
            if extension in language.get_file_extensions():
                detected_languages.append(language)
        
        return detected_languages
    
    @classmethod
    def from_codeql_identifier(cls, identifier: str) -> List['Language']:
        """Get languages that map to a CodeQL identifier."""
        languages = []
        for language in cls:
            if language.get_codeql_identifier() == identifier.lower():
                languages.append(language)
        return languages
    
    @classmethod
    def get_all_supported_by_codeql(cls) -> List['Language']:
        """Get all languages currently supported by CodeQL."""
        return list(cls)