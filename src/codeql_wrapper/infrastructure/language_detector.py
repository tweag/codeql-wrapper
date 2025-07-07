"""Language detector infrastructure module."""

from pathlib import Path
from typing import List, Set, Union, Optional, Dict
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
        self._non_compiled_extensions = {
            "js": "javascript",
            "ts": "typescript",
            "tsx": "typescript",
            "mts": "typescript",
            "cts": "typescript",
            "py": "python",
            "rb": "ruby",
        }

        self._compiled_extensions = {
            "java": "java",
            "cpp": "cpp",
            "c": "cpp",
            "h": "cpp",
            "hpp": "cpp",
            "c++": "cpp",
            "cxx": "cpp",
            "hh": "cpp",
            "h++": "cpp",
            "hxx": "cpp",
            "cc": "cpp",
            "cs": "csharp",
            "sln": "csharp",
            "csproj": "csharp",
            "cshtml": "csharp",
            "xaml": "csharp",
            "go": "go",
            "swift": "swift",
        }

    def detect_languages(
        self, target_dir: Union[str, Path], language_type: LanguageType
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
        target_path = Path(target_dir)

        if not target_path.exists():
            raise FileNotFoundError(f"Target directory does not exist: {target_dir}")

        if not target_path.is_dir():
            raise ValueError(f"Target path is not a directory: {target_dir}")

        self.logger.info(
            f"Detecting {language_type.name.lower()} languages in: {target_dir}"
        )

        detected_languages: Set[str] = set()

        try:
            for file_path in target_path.rglob("*"):
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

    def detect_all_languages(self, target_dir: Union[str, Path]) -> dict:
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

        # Special case: GitHub Actions workflows
        if language_type == LanguageType.NON_COMPILED and extension in ["yml", "yaml"]:
            # Check if the file is in .github/workflows directory
            parts = file_path.parts
            if len(parts) >= 3 and parts[-3:-1] == (".github", "workflows"):
                return "actions"

        if language_type == LanguageType.NON_COMPILED:
            result = self._non_compiled_extensions.get(extension)
            return result if result is not None else ""
        elif language_type == LanguageType.COMPILED:
            result = self._compiled_extensions.get(extension)
            return result if result is not None else ""

        return ""

    def get_supported_languages(
        self, language_type: Optional[LanguageType] = None
    ) -> Dict[str, str]:
        """
        Get all supported languages and their extensions.

        Args:
            language_type: Type of languages to get. If None, returns all.

        Returns:
            Dictionary mapping extensions to languages
        """
        if language_type == LanguageType.NON_COMPILED:
            return self._non_compiled_extensions.copy()
        elif language_type == LanguageType.COMPILED:
            return self._compiled_extensions.copy()
        else:
            # Return all extensions
            all_extensions = {}
            all_extensions.update(self._non_compiled_extensions)
            all_extensions.update(self._compiled_extensions)
            return all_extensions

    def format_languages_as_string(self, languages: List[str]) -> str:
        """
        Format a list of languages as a comma-separated string.

        Args:
            languages: List of language names

        Returns:
            Comma-separated string of languages, or empty string if no languages
        """
        if not languages:
            return ""
        return ",".join(languages)
