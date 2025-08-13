"""Language detector implementation."""

import logging
from pathlib import Path
from typing import Dict, Optional, Set

from codeql_wrapper_v2.domain.enumerators.language import Language
from codeql_wrapper_v2.domain.interfaces.project_detector import LanguageDetector


class LanguageDetectorImpl(LanguageDetector):
    """Implementation for detecting programming languages in projects."""
    
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        """Initialize the language detector."""
        self._logger = logger or logging.getLogger(__name__)
        
        # Framework indicators for more accurate language detection
        self._framework_indicators = {
            # JavaScript/TypeScript frameworks
            "package.json": [Language.JAVASCRIPT, Language.TYPESCRIPT],
            "tsconfig.json": [Language.TYPESCRIPT],
            "webpack.config.js": [Language.JAVASCRIPT],
            "vite.config.ts": [Language.TYPESCRIPT],
            "next.config.js": [Language.JAVASCRIPT],
            
            # Python frameworks
            "requirements.txt": [Language.PYTHON],
            "pyproject.toml": [Language.PYTHON],
            "setup.py": [Language.PYTHON],
            "poetry.lock": [Language.PYTHON],
            "Pipfile": [Language.PYTHON],
            
            # Java frameworks
            "pom.xml": [Language.JAVA],
            "build.gradle": [Language.JAVA, Language.KOTLIN],
            
            # .NET frameworks
            "*.csproj": [Language.CSHARP],
            "*.sln": [Language.CSHARP],
            
            # Go
            "go.mod": [Language.GO],
            
            # Rust
            "Cargo.toml": [Language.RUST],
            
            # Swift
            "Package.swift": [Language.SWIFT],
            
            # Ruby
            "Gemfile": [Language.RUBY],
        }
    
    async def detect_languages(self, project_path: Path) -> Set[Language]:
        """Detect programming languages in a project directory."""
        try:
            detected_languages = set()
            
            # First, detect by file extensions
            extension_languages = await self._detect_by_extensions(project_path)
            detected_languages.update(extension_languages)
            
            # Then, enhance detection with framework indicators
            framework_languages = await self._detect_by_frameworks(project_path)
            detected_languages.update(framework_languages)
            
            # Filter out unsupported languages and log results
            supported_languages = {
                lang for lang in detected_languages 
                if lang in Language.get_all_supported_by_codeql()
            }
            
            if supported_languages:
                lang_names = [lang.get_codeql_identifier() for lang in supported_languages]
                self._logger.debug(f"Detected languages in {project_path.name}: {lang_names}")
            else:
                self._logger.debug(f"No supported languages detected in {project_path.name}")
            
            return supported_languages
            
        except Exception as e:
            self._logger.error(f"Language detection failed for {project_path}: {e}")
            return set()
    
    async def detect_primary_language(self, project_path: Path) -> Language:
        """Detect the primary programming language in a project."""
        detected_languages = await self.detect_languages(project_path)
        
        if not detected_languages:
            raise ValueError(f"No languages detected in {project_path}")
        
        # Priority order for primary language selection
        priority_order = [
            Language.JAVA,      # Enterprise applications
            Language.CSHARP,    # Enterprise applications
            Language.PYTHON,    # Popular for many domains
            Language.TYPESCRIPT, # Modern web development
            Language.JAVASCRIPT, # Web development
            Language.GO,        # Modern systems programming
            Language.RUST,      # Systems programming
            Language.CPP,       # Systems programming
            Language.C,         # Systems programming
            Language.SWIFT,     # iOS development
            Language.KOTLIN,    # Android development
            Language.RUBY,      # Web development
        ]
        
        # Find the highest priority language that was detected
        for lang in priority_order:
            if lang in detected_languages:
                return lang
        
        # Fallback to first detected language
        return next(iter(detected_languages))
    
    async def _detect_by_extensions(self, project_path: Path) -> Set[Language]:
        """Detect languages by analyzing file extensions."""
        detected_languages = set()
        
        try:
            # Count files by extension to avoid false positives
            extension_counts: Dict[Language, int] = {}
            
            # Search for files with relevant extensions
            for file_path in project_path.rglob('*'):
                if file_path.is_file() and not self._should_skip_file(file_path):
                    extension = file_path.suffix.lower()
                    
                    # Detect languages for this extension
                    languages = Language.detect_from_extension(extension)
                    for lang in languages:
                        extension_counts[lang] = extension_counts.get(lang, 0) + 1
            
            # Only include languages with sufficient file count
            min_file_threshold = 1  # At least 1 file
            for lang, count in extension_counts.items():
                if count >= min_file_threshold:
                    detected_languages.add(lang)
            
            return detected_languages
            
        except Exception as e:
            self._logger.error(f"Extension-based detection failed for {project_path}: {e}")
            return set()
    
    async def _detect_by_frameworks(self, project_path: Path) -> Set[Language]:
        """Detect languages by analyzing framework indicators."""
        detected_languages = set()
        
        try:
            for indicator, languages in self._framework_indicators.items():
                if "*" in indicator:
                    # Handle glob patterns
                    matches = list(project_path.glob(indicator))
                    if matches:
                        detected_languages.update(languages)
                else:
                    # Handle exact file names
                    indicator_path = project_path / indicator
                    if indicator_path.exists():
                        detected_languages.update(languages)
            
            return detected_languages
            
        except Exception as e:
            self._logger.error(f"Framework-based detection failed for {project_path}: {e}")
            return set()
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if a file should be skipped during language detection."""
        # Skip hidden files and directories
        if any(part.startswith('.') for part in file_path.parts):
            return True
        
        # Skip common non-source directories
        skip_dirs = {
            'node_modules', '__pycache__', '.pytest_cache', 'target', 'build', 
            'dist', 'out', 'bin', 'obj', '.git', '.vscode', '.idea'
        }
        
        if any(part in skip_dirs for part in file_path.parts):
            return True
        
        # Skip binary and generated files
        skip_extensions = {
            '.exe', '.dll', '.so', '.dylib', '.a', '.lib', '.jar', '.war', 
            '.zip', '.tar', '.gz', '.bz2', '.7z', '.rar',
            '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.ico',
            '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'
        }
        
        if file_path.suffix.lower() in skip_extensions:
            return True
        
        return False
