"""Test cases for the LanguageDetector infrastructure class."""

import pytest
import tempfile
from pathlib import Path

from src.codeql_wrapper.infrastructure.language_detector import (
    LanguageDetector,
    LanguageType,
)


class TestLanguageDetector:
    """Test cases for LanguageDetector class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.detector = LanguageDetector()

    def test_language_detector_initialization(self):
        """Test that LanguageDetector initializes correctly."""
        assert self.detector is not None
        assert hasattr(self.detector, "logger")

    def test_detect_languages_with_sample_files(self):
        """Test language detection with sample files in a temporary directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create sample files
            (temp_path / "script.py").touch()
            (temp_path / "app.js").touch()
            (temp_path / "main.java").touch()
            (temp_path / "utils.cpp").touch()
            (temp_path / "config.ts").touch()
            (temp_path / "service.cs").touch()
            (temp_path / "README.md").touch()  # Should be ignored

            # Test non-compiled languages
            non_compiled = self.detector.detect_languages(
                temp_path, LanguageType.NON_COMPILED
            )
            expected_non_compiled = ["javascript", "python", "typescript"]
            assert sorted(non_compiled) == sorted(expected_non_compiled)

            # Test compiled languages
            compiled = self.detector.detect_languages(temp_path, LanguageType.COMPILED)
            expected_compiled = ["cpp", "csharp", "java"]
            assert sorted(compiled) == sorted(expected_compiled)

    def test_detect_all_languages(self):
        """Test detecting all languages at once."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create sample files
            (temp_path / "script.py").touch()
            (temp_path / "main.java").touch()

            result = self.detector.detect_all_languages(temp_path)

            assert "non_compiled" in result
            assert "compiled" in result
            assert "python" in result["non_compiled"]
            assert "java" in result["compiled"]

    def test_detect_languages_empty_directory(self):
        """Test language detection in an empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.detector.detect_languages(temp_dir, LanguageType.NON_COMPILED)
            assert result == []

    def test_detect_languages_nonexistent_directory(self):
        """Test language detection with non-existent directory."""
        with pytest.raises(FileNotFoundError):
            self.detector.detect_languages(
                "/nonexistent/directory", LanguageType.NON_COMPILED
            )

    def test_detect_languages_file_instead_of_directory(self):
        """Test language detection when given a file instead of directory."""
        with tempfile.NamedTemporaryFile() as temp_file:
            with pytest.raises(ValueError):
                self.detector.detect_languages(
                    temp_file.name, LanguageType.NON_COMPILED
                )

    def test_get_language_from_file(self):
        """Test getting language from file extension."""
        # Test non-compiled languages
        result = self.detector._get_language_from_file(
            Path("test.py"), LanguageType.NON_COMPILED
        )
        assert result == "python"

        result = self.detector._get_language_from_file(
            Path("app.js"), LanguageType.NON_COMPILED
        )
        assert result == "javascript"

        # Test compiled languages
        result = self.detector._get_language_from_file(
            Path("main.java"), LanguageType.COMPILED
        )
        assert result == "java"

        result = self.detector._get_language_from_file(
            Path("utils.cpp"), LanguageType.COMPILED
        )
        assert result == "cpp"

        # Test unsupported extension
        result = self.detector._get_language_from_file(
            Path("readme.txt"), LanguageType.NON_COMPILED
        )
        assert result == ""

    def test_cpp_extensions(self):
        """Test that all C++ extensions are detected correctly."""
        cpp_extensions = [
            "cpp",
            "c",
            "h",
            "hpp",
            "c++",
            "cxx",
            "hh",
            "h++",
            "hxx",
            "cc",
        ]

        for ext in cpp_extensions:
            result = self.detector._get_language_from_file(
                Path(f"test.{ext}"), LanguageType.COMPILED
            )
            assert result == "cpp", f"Extension .{ext} should map to cpp"

    def test_csharp_extensions(self):
        """Test that all C# extensions are detected correctly."""
        csharp_extensions = ["cs", "sln", "csproj", "cshtml", "xaml"]

        for ext in csharp_extensions:
            result = self.detector._get_language_from_file(
                Path(f"test.{ext}"), LanguageType.COMPILED
            )
            assert result == "csharp", f"Extension .{ext} should map to csharp"

    def test_typescript_extensions(self):
        """Test that all TypeScript extensions are detected correctly."""
        ts_extensions = ["ts", "tsx", "mts", "cts"]

        for ext in ts_extensions:
            result = self.detector._get_language_from_file(
                Path(f"test.{ext}"), LanguageType.NON_COMPILED
            )
            assert result == "typescript", f"Extension .{ext} should map to typescript"

    def test_get_supported_languages(self):
        """Test getting supported languages."""
        # Test non-compiled languages
        non_compiled = self.detector.get_supported_languages(LanguageType.NON_COMPILED)
        assert "py" in non_compiled
        assert non_compiled["py"] == "python"
        assert "java" not in non_compiled

        # Test compiled languages
        compiled = self.detector.get_supported_languages(LanguageType.COMPILED)
        assert "java" in compiled
        assert compiled["java"] == "java"
        assert "py" not in compiled

        # Test all languages
        all_langs = self.detector.get_supported_languages()
        assert "py" in all_langs
        assert "java" in all_langs

    def test_format_languages_as_string(self):
        """Test formatting languages as string."""
        # Test with multiple languages
        languages = ["python", "java", "javascript"]
        result = self.detector.format_languages_as_string(languages)
        assert result == "python,java,javascript"

        # Test with single language
        languages = ["python"]
        result = self.detector.format_languages_as_string(languages)
        assert result == "python"

        # Test with empty list
        languages = []
        result = self.detector.format_languages_as_string(languages)
        assert result == ""

    def test_subdirectory_scanning(self):
        """Test that subdirectories are scanned correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create nested directory structure
            subdir = temp_path / "subdir" / "nested"
            subdir.mkdir(parents=True)

            # Create files in different directories
            (temp_path / "root.py").touch()
            (temp_path / "subdir" / "middle.js").touch()
            (subdir / "deep.java").touch()

            # Test detection includes all subdirectories
            all_languages = self.detector.detect_all_languages(temp_path)

            assert "python" in all_languages["non_compiled"]
            assert "javascript" in all_languages["non_compiled"]
            assert "java" in all_languages["compiled"]

    def test_case_insensitive_extensions(self):
        """Test that file extensions are handled case-insensitively."""
        # Test uppercase extensions
        result = self.detector._get_language_from_file(
            Path("test.PY"), LanguageType.NON_COMPILED
        )
        assert result == "python"

        result = self.detector._get_language_from_file(
            Path("test.JAVA"), LanguageType.COMPILED
        )
        assert result == "java"

        # Test mixed case
        result = self.detector._get_language_from_file(
            Path("test.Cpp"), LanguageType.COMPILED
        )
        assert result == "cpp"

    def test_github_actions_detection(self) -> None:
        """Test GitHub Actions workflow detection."""
        # Test .yml file in .github/workflows should be detected as actions
        result = self.detector._get_language_from_file(
            Path(".github/workflows/test.yml"), LanguageType.NON_COMPILED
        )
        assert result == "actions"

        # Test .yaml file in .github/workflows should be detected as actions
        result = self.detector._get_language_from_file(
            Path(".github/workflows/ci.yaml"), LanguageType.NON_COMPILED
        )
        assert result == "actions"

        # Test yml file NOT in .github/workflows should NOT be detected as actions
        result = self.detector._get_language_from_file(
            Path("config.yml"), LanguageType.NON_COMPILED
        )
        assert result == ""

        # Test yml file in different directory should NOT be detected as actions
        result = self.detector._get_language_from_file(
            Path("config/workflows/test.yml"), LanguageType.NON_COMPILED
        )
        assert result == ""

        # Test yml file in .github but not workflows should NOT be detected as actions
        result = self.detector._get_language_from_file(
            Path(".github/dependabot.yml"), LanguageType.NON_COMPILED
        )
        assert result == ""

        # Test compiled language type should ignore actions
        result = self.detector._get_language_from_file(
            Path(".github/workflows/test.yml"), LanguageType.COMPILED
        )
        assert result == ""

    def test_detect_github_actions_in_directory(self) -> None:
        """Test detecting GitHub Actions workflows in a real directory structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create .github/workflows directory structure
            github_dir = temp_path / ".github" / "workflows"
            github_dir.mkdir(parents=True)

            # Create workflow files
            workflow_yml = github_dir / "ci.yml"
            workflow_yml.write_text(
                "name: CI\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest"
            )

            workflow_yaml = github_dir / "deploy.yaml"
            workflow_yaml.write_text(
                "name: Deploy\non: [push]\njobs:\n  deploy:\n    runs-on: ubuntu-latest"
            )

            # Create a regular yml file outside workflows
            config_yml = temp_path / "config.yml"
            config_yml.write_text("key: value")

            # Create some other language files
            python_file = temp_path / "test.py"
            python_file.write_text("print('hello')")

            # Detect languages
            result = self.detector.detect_languages(
                temp_path, LanguageType.NON_COMPILED
            )

            # Should detect both actions and python
            assert "actions" in result
            assert "python" in result
            assert len(result) == 2
