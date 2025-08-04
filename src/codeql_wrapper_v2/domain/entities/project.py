"""Project entity for CodeQL analysis domain."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Set

from ..enumerators.language import Language


@dataclass(frozen=True)
class Project:
    """Represents a project within a repository with immutable state and rich behavior."""
    
    # Core identity
    name: str
    project_path: Path
    repository_path: Path
    
    # Language information
    detected_languages: Set[Language] = field(default_factory=set)
    target_language: Optional[Language] = None
    
    # Build configuration
    build_mode: str = "none"  # none, manual, autobuild
    build_script_path: Optional[Path] = None
    
    # Analysis configuration
    queries: List[str] = field(default_factory=list)
    
    # Project metadata
    framework: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Validate project state on creation."""
        if not self.name or not self.name.strip():
            raise ValueError("Project name cannot be empty")
        
        if not self.project_path.exists():
            raise ValueError(f"Project path does not exist: {self.project_path}")
        
        if not self.repository_path.exists():
            raise ValueError(f"Repository path does not exist: {self.repository_path}")
        
        # Validate project path is within repository
        try:
            self.project_path.relative_to(self.repository_path)
        except ValueError:
            raise ValueError("Project path must be within repository path")
    
    def has_language(self, language: Language) -> bool:
        """Check if project contains a specific language."""
        return language in self.detected_languages
    
    def has_compiled_languages(self) -> bool:
        """Check if project contains any compiled languages."""
        return any(lang.is_compiled_language() for lang in self.detected_languages)
    
    def has_non_compiled_languages(self) -> bool:
        """Check if project contains any non-compiled languages."""
        return any(not lang.is_compiled_language() for lang in self.detected_languages)
    
    def get_compiled_languages(self) -> Set[Language]:
        """Get all compiled languages in the project."""
        return {lang for lang in self.detected_languages if lang.is_compiled_language()}
    
    def get_non_compiled_languages(self) -> Set[Language]:
        """Get all non-compiled languages in the project."""
        return {lang for lang in self.detected_languages if not lang.is_compiled_language()}
    
    def get_codeql_languages(self) -> Set[str]:
        """Get CodeQL identifiers for all detected languages."""
        return {lang.get_codeql_identifier() for lang in self.detected_languages}
    
    def requires_build(self) -> bool:
        """Check if project requires build steps."""
        return (
            self.build_mode in ("manual", "autobuild") or 
            self.has_compiled_languages()
        )
    
    def get_relative_path(self) -> Path:
        """Get project path relative to repository root."""
        return self.project_path.relative_to(self.repository_path)
    
    def is_valid_for_analysis(self) -> bool:
        """Check if project is valid for CodeQL analysis."""
        return (
            len(self.detected_languages) > 0 and
            self.project_path.exists() and
            self.project_path.is_dir()
        )
    
    def get_analysis_languages(self) -> Set[Language]:
        """Get languages that should be analyzed."""
        if self.target_language:
            return {self.target_language} if self.target_language in self.detected_languages else set()
        return self.detected_languages
    
    def get_display_name(self) -> str:
        """Get a display-friendly name for the project."""
        if self.target_language:
            return f"{self.name}({self.target_language.get_codeql_identifier()})"
        return self.name
