"""Test cases for the LanguageDetector infrastructure class."""

import pytest
import tempfile
from pathlib import Path

from codeql_wrapper.infrastructure.language_detector import (
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

    def test_permission_error_handling(self) -> None:
        """Test handling of permission errors during directory scanning."""
        from unittest.mock import patch

        # Mock pathlib.rglob to raise PermissionError
        with patch.object(Path, "rglob") as mock_rglob:
            mock_rglob.side_effect = PermissionError("Access denied")

            with tempfile.TemporaryDirectory() as temp_dir:
                with pytest.raises(PermissionError, match="Access denied"):
                    self.detector.detect_languages(temp_dir, LanguageType.NON_COMPILED)

    def test_edge_case_extensions(self) -> None:
        """Test edge cases with file extensions."""
        # Test file with no extension
        result = self.detector._get_language_from_file(
            Path("README"), LanguageType.NON_COMPILED
        )
        assert result == ""

        # Test file with only dot
        result = self.detector._get_language_from_file(
            Path("."), LanguageType.NON_COMPILED
        )
        assert result == ""

        # Test file with multiple dots
        result = self.detector._get_language_from_file(
            Path("test.min.js"), LanguageType.NON_COMPILED
        )
        assert result == "javascript"

        # Test hidden file with extension
        result = self.detector._get_language_from_file(
            Path(".gitignore.py"), LanguageType.NON_COMPILED
        )
        assert result == "python"

    def test_ruby_language_detection(self) -> None:
        """Test Ruby language detection."""
        result = self.detector._get_language_from_file(
            Path("app.rb"), LanguageType.NON_COMPILED
        )
        assert result == "ruby"

        # Test uppercase
        result = self.detector._get_language_from_file(
            Path("test.RB"), LanguageType.NON_COMPILED
        )
        assert result == "ruby"

    def test_go_language_detection(self) -> None:
        """Test Go language detection."""
        result = self.detector._get_language_from_file(
            Path("main.go"), LanguageType.COMPILED
        )
        assert result == "go"

        # Test uppercase
        result = self.detector._get_language_from_file(
            Path("test.GO"), LanguageType.COMPILED
        )
        assert result == "go"

    def test_swift_language_detection(self) -> None:
        """Test Swift language detection."""
        result = self.detector._get_language_from_file(
            Path("ViewController.swift"), LanguageType.COMPILED
        )
        assert result == "swift"

        # Test uppercase
        result = self.detector._get_language_from_file(
            Path("test.SWIFT"), LanguageType.COMPILED
        )
        assert result == "swift"

    def test_language_type_filtering(self) -> None:
        """Test that language type filtering works correctly."""
        # Test JavaScript (non-compiled) shouldn't be detected as compiled
        result = self.detector._get_language_from_file(
            Path("app.js"), LanguageType.COMPILED
        )
        assert result == ""

        # Test Java (compiled) shouldn't be detected as non-compiled
        result = self.detector._get_language_from_file(
            Path("Main.java"), LanguageType.NON_COMPILED
        )
        assert result == ""

    def test_comprehensive_directory_structure(self) -> None:
        """Test language detection with a comprehensive directory structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create complex directory structure
            dirs = [
                "src/main/java",
                "src/main/resources",
                "frontend/src/components",
                "backend/api",
                "scripts",
                ".github/workflows",
                "docs",
            ]

            for dir_path in dirs:
                (temp_path / dir_path).mkdir(parents=True, exist_ok=True)

            # Create various language files
            files = [
                ("src/main/java/Application.java", "java"),
                ("src/main/java/Service.java", "java"),
                ("frontend/src/components/App.js", "javascript"),
                ("frontend/src/components/Header.tsx", "typescript"),
                ("backend/api/server.py", "python"),
                ("backend/api/utils.py", "python"),
                ("scripts/deploy.rb", "ruby"),
                ("scripts/build.go", "go"),
                ("src/main/resources/native.cpp", "cpp"),
                ("src/main/resources/helper.h", "cpp"),
                ("frontend/src/App.cs", "csharp"),
                ("backend/api/models.swift", "swift"),
                (".github/workflows/ci.yml", "actions"),
                (".github/workflows/deploy.yaml", "actions"),
                ("docs/README.md", None),  # Should be ignored
                ("config.xml", None),  # Should be ignored
            ]

            for file_path, _ in files:
                (temp_path / file_path).touch()

            # Test non-compiled languages
            non_compiled = self.detector.detect_languages(
                temp_path, LanguageType.NON_COMPILED
            )
            expected_non_compiled = [
                "actions",
                "javascript",
                "python",
                "ruby",
                "typescript",
            ]
            assert sorted(non_compiled) == sorted(expected_non_compiled)

            # Test compiled languages
            compiled = self.detector.detect_languages(temp_path, LanguageType.COMPILED)
            expected_compiled = ["cpp", "csharp", "go", "java", "swift"]
            assert sorted(compiled) == sorted(expected_compiled)

            # Test all languages
            all_result = self.detector.detect_all_languages(temp_path)
            assert sorted(all_result["non_compiled"]) == sorted(expected_non_compiled)
            assert sorted(all_result["compiled"]) == sorted(expected_compiled)

    def test_empty_and_whitespace_extensions(self) -> None:
        """Test handling of empty and whitespace-only extensions."""
        # Test empty extension
        result = self.detector._get_language_from_file(
            Path("file."), LanguageType.NON_COMPILED
        )
        assert result == ""

        # Test extension with just whitespace (edge case)
        result = self.detector._get_language_from_file(
            Path("file. "), LanguageType.NON_COMPILED
        )
        assert result == ""

    def test_symlink_handling(self) -> None:
        """Test that symlinks are handled correctly during directory scanning."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a real file
            real_file = temp_path / "real.py"
            real_file.write_text("print('hello')")

            # Create a directory with a file
            subdir = temp_path / "subdir"
            subdir.mkdir()
            subdir_file = subdir / "script.js"
            subdir_file.write_text("console.log('hi');")

            try:
                # Create symlinks (if supported by the OS)
                symlink_file = temp_path / "link.py"
                symlink_file.symlink_to(real_file)

                symlink_dir = temp_path / "linkdir"
                symlink_dir.symlink_to(subdir)
            except (OSError, NotImplementedError):
                # Skip test if symlinks not supported
                pytest.skip("Symlinks not supported on this system")

            # Detect languages - should handle symlinks gracefully
            result = self.detector.detect_languages(
                temp_path, LanguageType.NON_COMPILED
            )

            # Should detect both python and javascript
            assert "python" in result
            assert "javascript" in result

    def test_very_deep_directory_structure(self) -> None:
        """Test language detection with very deep directory nesting."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create deeply nested structure
            deep_path = temp_path
            for i in range(10):  # 10 levels deep
                deep_path = deep_path / f"level{i}"
                deep_path.mkdir()

            # Create a file at the deepest level
            deep_file = deep_path / "deep.py"
            deep_file.write_text("# Deep file")

            # Should still detect the language
            result = self.detector.detect_languages(
                temp_path, LanguageType.NON_COMPILED
            )
            assert "python" in result

    def test_special_characters_in_filenames(self) -> None:
        """Test handling of special characters in filenames."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create files with special characters
            special_files = [
                "файл.py",  # Unicode
                "file-name.js",  # Hyphen
                "file_name.java",  # Underscore
                "file name.cpp",  # Space (if supported)
                "file.backup.rb",  # Multiple dots
            ]

            created_files = []
            for filename in special_files:
                try:
                    file_path = temp_path / filename
                    file_path.write_text("// test")
                    created_files.append(filename)
                except (OSError, UnicodeEncodeError):
                    # Skip files that can't be created on this system
                    continue

            if not created_files:
                pytest.skip("No special character files could be created")

            # Should detect languages regardless of special characters
            all_result = self.detector.detect_all_languages(temp_path)
            detected_all = all_result["non_compiled"] + all_result["compiled"]

            # Should have detected at least some languages
            assert len(detected_all) > 0

    def test_case_sensitivity_comprehensive(self) -> None:
        """Test comprehensive case sensitivity handling."""
        test_cases = [
            ("test.PY", "python", LanguageType.NON_COMPILED),
            ("test.Py", "python", LanguageType.NON_COMPILED),
            ("test.pY", "python", LanguageType.NON_COMPILED),
            ("TEST.JS", "javascript", LanguageType.NON_COMPILED),
            ("APP.JAVA", "java", LanguageType.COMPILED),
            ("MAIN.CPP", "cpp", LanguageType.COMPILED),
            ("Service.CS", "csharp", LanguageType.COMPILED),
            ("script.RB", "ruby", LanguageType.NON_COMPILED),
            ("main.GO", "go", LanguageType.COMPILED),
            ("view.SWIFT", "swift", LanguageType.COMPILED),
        ]

        for filename, expected_lang, lang_type in test_cases:
            result = self.detector._get_language_from_file(Path(filename), lang_type)
            assert result == expected_lang, f"Failed for {filename}"

    def test_github_actions_edge_cases(self) -> None:
        """Test edge cases for GitHub Actions detection."""
        # Test path with fewer than 3 components (our fix)
        result = self.detector._get_language_from_file(
            Path("workflows/test.yml"), LanguageType.NON_COMPILED
        )
        assert result == ""

        # Test path with exactly 3 components but not .github/workflows
        result = self.detector._get_language_from_file(
            Path("some/other/test.yml"), LanguageType.NON_COMPILED
        )
        assert result == ""

        # Test .github/workflows with extra nesting
        result = self.detector._get_language_from_file(
            Path("repo/.github/workflows/ci.yml"), LanguageType.NON_COMPILED
        )
        assert result == "actions"

    def test_logger_usage(self) -> None:
        """Test that logger is used appropriately."""
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "test.py").touch()

            # Mock the logger to verify it's called
            with patch.object(self.detector, "logger") as mock_logger:
                result = self.detector.detect_languages(
                    temp_path, LanguageType.NON_COMPILED
                )

                # Verify logger.info was called
                assert (
                    mock_logger.info.call_count >= 2
                )  # At least start and end logging
                assert "python" in result

    def test_initialization_state(self) -> None:
        """Test that initialization creates the expected internal state."""
        detector = LanguageDetector()

        # Verify internal mappings are properly initialized
        assert hasattr(detector, "_non_compiled_extensions")
        assert hasattr(detector, "_compiled_extensions")
        assert hasattr(detector, "logger")

        # Verify some expected mappings
        assert detector._non_compiled_extensions["py"] == "python"
        assert detector._non_compiled_extensions["js"] == "javascript"
        assert detector._compiled_extensions["java"] == "java"
        assert detector._compiled_extensions["cpp"] == "cpp"

        # Verify no overlap between compiled and non-compiled
        non_compiled_keys = set(detector._non_compiled_extensions.keys())
        compiled_keys = set(detector._compiled_extensions.keys())
        overlap = non_compiled_keys.intersection(compiled_keys)
        assert len(overlap) == 0, f"Found overlapping extensions: {overlap}"

    def test_invalid_language_type_edge_case(self) -> None:
        """Test handling of invalid language type (edge case for 100% coverage)."""
        # This test is primarily for coverage of the final return statement
        # In practice, this case shouldn't occur since LanguageType is an Enum
        # But we can still test it by directly calling the method with a mock
        from unittest.mock import Mock

        # Create a mock that doesn't match either LanguageType value
        mock_type = Mock()
        mock_type.__eq__ = Mock(
            return_value=False
        )  # Won't equal NON_COMPILED or COMPILED

        # Use type: ignore to bypass type checking for this edge case test
        result = self.detector._get_language_from_file(
            Path("test.py"), mock_type  # type: ignore
        )
        assert result == ""

    def test_file_extension_with_leading_dots(self) -> None:
        """Test handling of files with multiple leading dots."""
        # Test file starting with multiple dots
        result = self.detector._get_language_from_file(
            Path("...hidden.py"), LanguageType.NON_COMPILED
        )
        assert result == "python"

        # Test file with dots in directory path
        result = self.detector._get_language_from_file(
            Path("../parent/test.js"), LanguageType.NON_COMPILED
        )
        assert result == "javascript"
