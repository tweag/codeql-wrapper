"""Language detector infrastructure module."""

from pathlib import Path
from typing import List, Set
from enum import Enum

from .logger import get_logger


class LanguageType(Enum):
    """Enum for language types."""

    NON_COMPILED = 0
    COMPILED = 1


class LanguageDetector:
    """Detects programming languages in a directory based on file extensions."""

    def __init__(self) -> None:
        """Initialize the language detector."""
        self.logger = get_logger(__name__)

        # Define language mappings based on file extensions
        # Following CodeQL Action's exact language mapping from languages.ts
        # Non-compiled languages (interpreted/transpiled)
        self._non_compiled_extensions = {
            # JavaScript (includes TypeScript - CodeQL treats them identically)
            # Note: TypeScript is treated as JavaScript in CodeQL Action
            # Note: JSX, Flow, HTML, and other web-related files are analyzed with JavaScript
            "js": "javascript",
            "jsx": "javascript",
            "mjs": "javascript",
            "es": "javascript",
            "es6": "javascript",
            "ts": "javascript",  # TypeScript → JavaScript
            "tsx": "javascript",  # TypeScript → JavaScript
            "mts": "javascript",  # TypeScript → JavaScript
            "cts": "javascript",  # TypeScript → JavaScript
            "htm": "javascript",
            "html": "javascript",
            "xhtm": "javascript",
            "xhtml": "javascript",
            "vue": "javascript",
            "hbs": "javascript",
            "ejs": "javascript",
            "njk": "javascript",
            "raml": "javascript",
            # Python (2.7, 3.5-3.13)
            # Note: The extractor requires Python 3 to run. To analyze Python 2.7
            # you should install both versions of Python
            "py": "python",
            # Ruby (up to 3.3)
            "rb": "ruby",
            "erb": "ruby",
            "gemspec": "ruby",
            # Rust (editions 2021 and 2024)
            # Note: Requires rustup and cargo to be installed
            # Note: Features from nightly toolchains are not supported
            "rs": "rust",
        }

        # Compiled languages (traced languages in CodeQL Action)
        self._compiled_extensions = {
            # C/C++ (C89-C23, C++98-C++23)
            # Note: C++20 modules are not supported
            # Note: C23 and C++23 support is currently in beta
            # Note: Objective-C, Objective-C++, C++/CLI, and C++/CX are not supported
            # Note: Support for the clang-cl compiler is preliminary
            # Note: Support for the Arm Compiler (armcc) is preliminary
            "cpp": "cpp",
            "c++": "cpp",
            "cxx": "cpp",
            "hpp": "cpp",
            "hh": "cpp",
            "h++": "cpp",
            "hxx": "cpp",
            "c": "cpp",
            "cc": "cpp",
            "h": "cpp",
            # C# (up to C# 13)
            "sln": "csharp",
            "csproj": "csharp",
            "cs": "csharp",
            "cshtml": "csharp",
            "xaml": "csharp",
            # Go (up to 1.24)
            # Note: Requires glibc 2.17
            "go": "go",
            # Java (7-24) - includes Kotlin (Kotlin → Java in CodeQL Action)
            # Note: Builds that execute on Java 7 to 24 can be analyzed
            # Note: The analysis understands standard language features in Java 8
            # to 24; "preview" and "incubator" features are not supported
            # Note: Source code using Java language versions older than Java 8
            # are analyzed as Java 8 code
            # Note: ECJ is supported when the build invokes it via the Maven
            # Compiler plugin or the Takari Lifecycle plugin
            "java": "java",
            "kt": "java",  # Kotlin → Java (CodeQL Action treats Kotlin as Java)
            # Swift (5.4-6.1)
            # Note: Support for the analysis of Swift requires macOS
            "swift": "swift",
        }

    # Public methods first
    def detect_all_languages(self, target_dir: Path) -> dict:
        """
        Detect both compiled and non-compiled languages in a directory.

        Args:
            target_dir: Directory to scan for language files

        Returns:
            Dictionary with 'compiled' and 'non_compiled' keys containing language lists
        """
        return {
            "non_compiled": self.detect_languages(
                target_dir, LanguageType.NON_COMPILED
            ),
            "compiled": self.detect_languages(target_dir, LanguageType.COMPILED),
        }

    def detect_languages(
        self, target_dir: Path, language_type: LanguageType
    ) -> List[str]:
        """
        Detect programming languages in a directory.

        Args:
            target_dir: Directory to scan for language files
            language_type: Type of languages to detect (compiled or non-compiled)

        Returns:
            List of detected languages, sorted and deduplicated

        Raises:
            FileNotFoundError: If target directory doesn't exist
            PermissionError: If target directory is not accessible
        """

        if not target_dir.exists():
            raise FileNotFoundError(f"Target directory does not exist: {target_dir}")

        if not target_dir.is_dir():
            raise ValueError(f"Target path is not a directory: {target_dir}")

        self.logger.info(
            f"Detecting {language_type.name.lower()} languages in: {target_dir}"
        )

        detected_languages: Set[str] = set()

        try:
            for file_path in target_dir.rglob("*"):
                if file_path.is_file():
                    language = self._get_language_from_file(file_path, language_type)
                    if language:
                        detected_languages.add(language)
        except PermissionError as e:
            self.logger.error(f"Permission denied accessing directory: {e}")
            raise

        # Sort and return as list
        result = sorted(list(detected_languages))
        self.logger.info(f"Detected languages: {result}")
        return result

    # Private methods last
    def _get_language_from_file(
        self, file_path: Path, language_type: LanguageType
    ) -> str:
        """
        Get the language for a file based on its extension and type filter.

        Args:
            file_path: Path to the file
            language_type: Type of languages to consider

        Returns:
            Language name if detected, empty string otherwise
        """
        # Get file extension (without the dot)
        extension = file_path.suffix.lstrip(".").lower()

        if language_type == LanguageType.NON_COMPILED:
            result = self._non_compiled_extensions.get(extension)
            return result if result is not None else ""
        elif language_type == LanguageType.COMPILED:
            result = self._compiled_extensions.get(extension)
            return result if result is not None else ""

        return ""
