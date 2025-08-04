"""Project metadata entity for additional project information."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

from ..enumerators.language import Language


@dataclass(frozen=True)
class ProjectMetadata:
    """Metadata about a detected project including build and configuration information."""
    
    # Framework detection
    framework: Optional[str] = None
    framework_version: Optional[str] = None
    
    # Build system information
    build_files: Set[str] = field(default_factory=set)
    package_managers: Set[str] = field(default_factory=set)
    
    # Language-specific metadata
    language_versions: Dict[Language, Optional[str]] = field(default_factory=dict)
    
    # Configuration files
    config_files: Set[str] = field(default_factory=set)
    
    # Dependencies (simplified)
    has_dependencies: bool = False
    dependency_count: int = 0
    
    def add_build_file(self, file_path: str) -> None:
        """Add a detected build file."""
        # Since this is frozen, we need to work around immutability for builder pattern
        # In practice, this would be handled by a builder or factory
        pass
    
    def get_primary_language(self, detected_languages: Set[Language]) -> Optional[Language]:
        """Determine the primary language based on metadata."""
        if not detected_languages:
            return None
        
        # Priority based on framework detection
        if self.framework:
            framework_language_mapping = {
                "react": Language.JAVASCRIPT,
                "angular": Language.TYPESCRIPT,
                "vue": Language.JAVASCRIPT,
                "django": Language.PYTHON,
                "flask": Language.PYTHON,
                "spring": Language.JAVA,
                "dotnet": Language.CSHARP,
                ".net": Language.CSHARP,
            }
            
            framework_lower = self.framework.lower()
            for framework_key, language in framework_language_mapping.items():
                if framework_key in framework_lower and language in detected_languages:
                    return language
        
        # Priority based on build files
        build_file_language_mapping = {
            "pom.xml": Language.JAVA,
            "build.gradle": Language.JAVA,
            "package.json": Language.JAVASCRIPT,
            "tsconfig.json": Language.TYPESCRIPT,
            "requirements.txt": Language.PYTHON,
            "pyproject.toml": Language.PYTHON,
            "Cargo.toml": Language.RUST,
            "go.mod": Language.GO,
            "*.csproj": Language.CSHARP,
            "*.sln": Language.CSHARP,
        }
        
        for build_file in self.build_files:
            for pattern, language in build_file_language_mapping.items():
                if pattern in build_file and language in detected_languages:
                    return language
        
        # Return first detected language as fallback
        return next(iter(detected_languages))
    
    def is_web_project(self) -> bool:
        """Check if this appears to be a web project."""
        web_indicators = {
            "react", "angular", "vue", "express", "next.js", "nuxt", "svelte"
        }
        
        if self.framework:
            return any(indicator in self.framework.lower() for indicator in web_indicators)
        
        web_files = {"package.json", "webpack.config.js", "vite.config.js", "index.html"}
        return bool(web_files.intersection(self.build_files))
    
    def requires_build_step(self) -> bool:
        """Determine if project requires explicit build steps."""
        build_indicators = {
            "pom.xml", "build.gradle", "Cargo.toml", "go.mod", 
            "*.csproj", "*.sln", "CMakeLists.txt", "Makefile"
        }
        
        return bool(build_indicators.intersection(self.build_files))
    
    def get_suggested_build_mode(self) -> str:
        """Suggest build mode based on detected metadata."""
        if self.requires_build_step():
            return "autobuild"
        return "none"
