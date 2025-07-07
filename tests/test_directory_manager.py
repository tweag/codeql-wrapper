"""Test cases for the DirectoryManager infrastructure class."""

import pytest
import tempfile
import subprocess
import json
from pathlib import Path
from unittest.mock import patch

from codeql_wrapper.infrastructure.directory_manager import DirectoryManager


class TestDirectoryManager:
    """Test cases for DirectoryManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = DirectoryManager(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_directory_manager_initialization(self):
        """Test that DirectoryManager initializes correctly."""
        assert self.manager is not None
        assert hasattr(self.manager, "logger")
        assert self.manager.base_path == Path(self.temp_dir)

    def test_directory_manager_default_path(self):
        """Test DirectoryManager with default path."""
        default_manager = DirectoryManager()
        assert default_manager.base_path == Path.cwd()

    def test_list_all_directories(self):
        """Test listing all directories in a path."""
        temp_path = Path(self.temp_dir)

        # Create test directories
        (temp_path / "project1").mkdir()
        (temp_path / "project2").mkdir()
        (temp_path / ".hidden").mkdir()
        (temp_path / "nested" / "deep").mkdir(parents=True)

        # Create some files (should be ignored)
        (temp_path / "file.txt").touch()
        (temp_path / "project1" / "subfile.txt").touch()

        # Test excluding hidden directories (default)
        directories = self.manager.list_all_directories()
        expected = ["nested", "project1", "project2"]
        assert sorted(directories) == sorted(expected)

        # Test including hidden directories
        directories_with_hidden = self.manager.list_all_directories(
            exclude_hidden=False
        )
        expected_with_hidden = [".hidden", "nested", "project1", "project2"]
        assert sorted(directories_with_hidden) == sorted(expected_with_hidden)

    def test_list_all_directories_empty(self):
        """Test listing directories in an empty directory."""
        directories = self.manager.list_all_directories()
        assert directories == []

    def test_list_all_directories_nonexistent(self):
        """Test listing directories in a non-existent path."""
        manager = DirectoryManager("/nonexistent/path")
        with pytest.raises(FileNotFoundError):
            manager.list_all_directories()

    def test_list_all_directories_file_path(self):
        """Test listing directories when given a file path."""
        temp_path = Path(self.temp_dir)
        test_file = temp_path / "test.txt"
        test_file.touch()

        manager = DirectoryManager(test_file)
        with pytest.raises(ValueError):
            manager.list_all_directories()

    def test_to_json_array(self):
        """Test converting directory list to JSON array."""
        directories = ["project1", "project2", "utils"]
        json_result = self.manager.to_json_array(directories)

        # Parse back to verify it's valid JSON
        parsed = json.loads(json_result)
        assert parsed == directories

        # Test empty list
        empty_json = self.manager.to_json_array([])
        assert json.loads(empty_json) == []

    @patch("subprocess.run")
    def test_is_git_repository_true(self, mock_run):
        """Test detecting git repository when it exists."""
        mock_run.return_value.returncode = 0
        assert self.manager._is_git_repository() is True

    @patch("subprocess.run")
    def test_is_git_repository_false(self, mock_run):
        """Test detecting git repository when it doesn't exist."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        assert self.manager._is_git_repository() is False

    @patch("subprocess.run")
    def test_is_git_repository_file_not_found(self, mock_run):
        """Test detecting git repository when git command is not found."""
        mock_run.side_effect = FileNotFoundError()
        assert self.manager._is_git_repository() is False

    def test_determine_base_commit_pull_request(self):
        """Test determining base commit for pull request."""
        with patch.object(self.manager, "_run_git_command") as mock_git:
            base_commit = self.manager._determine_base_commit(
                github_event_name="pull_request", github_base_ref="main"
            )
            assert base_commit == "origin/main"
            mock_git.assert_called_once_with(["fetch", "origin", "main", "--depth=2"])

    def test_determine_base_commit_pull_request_fetch_fail(self):
        """Test determining base commit when fetch fails."""
        with patch.object(self.manager, "_run_git_command") as mock_git:
            mock_git.side_effect = subprocess.CalledProcessError(1, "git")

            base_commit = self.manager._determine_base_commit(
                github_event_name="pull_request", github_base_ref="main"
            )
            assert base_commit == "HEAD^"

    def test_determine_base_commit_push_event(self):
        """Test determining base commit for push event."""
        with patch.object(self.manager, "_run_git_command") as mock_git:
            base_commit = self.manager._determine_base_commit(github_event_name="push")
            assert base_commit == "HEAD^"
            mock_git.assert_called_once_with(["fetch", "origin", "--depth=2"])

    @patch("subprocess.run")
    def test_get_changed_files(self, mock_run):
        """Test getting changed files from git diff."""
        mock_run.return_value.stdout = (
            "project1/file1.py\nproject2/file2.js\nutils/helper.py\n"
        )
        mock_run.return_value.returncode = 0

        changed_files = self.manager._get_changed_files("HEAD^")
        expected = ["project1/file1.py", "project2/file2.js", "utils/helper.py"]
        assert changed_files == expected

    @patch("subprocess.run")
    def test_get_changed_files_git_error(self, mock_run):
        """Test getting changed files when git command fails."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        changed_files = self.manager._get_changed_files("HEAD^")
        assert changed_files == []

    def test_list_changed_directories_not_git_repo(self):
        """Test listing changed directories when not in a git repository."""
        with patch.object(self.manager, "_is_git_repository", return_value=False):
            with pytest.raises(FileNotFoundError):
                self.manager.list_changed_directories()

    @patch.object(DirectoryManager, "_is_git_repository", return_value=True)
    @patch.object(DirectoryManager, "_get_changed_files")
    @patch.object(DirectoryManager, "_determine_base_commit")
    def test_list_changed_directories(
        self, mock_base_commit, mock_changed_files, mock_is_git
    ):
        """Test listing changed directories successfully."""
        mock_base_commit.return_value = "HEAD^"
        mock_changed_files.return_value = [
            "project1/src/main.py",
            "project1/tests/test_main.py",
            "project2/app.js",
            "utils/helper.py",
            ".github/workflows/ci.yml",  # Should be excluded
        ]

        changed_dirs = self.manager.list_changed_directories()
        expected = ["project1", "project2", "utils"]
        assert sorted(changed_dirs) == sorted(expected)

    @patch.object(DirectoryManager, "_is_git_repository", return_value=True)
    @patch.object(DirectoryManager, "_get_changed_files")
    @patch.object(DirectoryManager, "_determine_base_commit")
    def test_list_changed_directories_include_hidden(
        self, mock_base_commit, mock_changed_files, mock_is_git
    ):
        """Test listing changed directories including hidden ones."""
        mock_base_commit.return_value = "HEAD^"
        mock_changed_files.return_value = [
            "project1/main.py",
            ".github/workflows/ci.yml",
            ".vscode/settings.json",
        ]

        changed_dirs = self.manager.list_changed_directories(exclude_hidden=False)
        expected = [".github", ".vscode", "project1"]
        assert sorted(changed_dirs) == sorted(expected)

    def test_get_directory_info_basic(self):
        """Test getting basic directory information."""
        temp_path = Path(self.temp_dir)
        (temp_path / "project1").mkdir()
        (temp_path / "project2").mkdir()

        info = self.manager.get_directory_info()

        assert info["base_path"] == str(self.temp_dir)
        assert "project1" in info["all_directories"]
        assert "project2" in info["all_directories"]
        assert "is_git_repository" in info

    @patch.object(DirectoryManager, "_is_git_repository", return_value=True)
    @patch.object(DirectoryManager, "list_changed_directories")
    def test_get_directory_info_with_changes(self, mock_changed_dirs, mock_is_git):
        """Test getting directory information including changes."""
        mock_changed_dirs.return_value = ["project1", "utils"]

        info = self.manager.get_directory_info(include_changed=True)

        assert info["is_git_repository"] is True
        assert info["changed_directories"] == ["project1", "utils"]

    @patch.object(DirectoryManager, "_is_git_repository", return_value=True)
    @patch.object(DirectoryManager, "list_changed_directories")
    def test_get_directory_info_git_error(self, mock_changed_dirs, mock_is_git):
        """Test getting directory info when git operations fail."""
        mock_changed_dirs.side_effect = subprocess.CalledProcessError(1, "git")

        info = self.manager.get_directory_info(include_changed=True)

        assert info["is_git_repository"] is True
        assert info["changed_directories"] == []

    def test_max_depth_parameter(self):
        """Test the max_depth parameter functionality."""
        temp_path = Path(self.temp_dir)

        # Create deep nested structure
        deep_path = temp_path / "level1" / "level2" / "level3"
        deep_path.mkdir(parents=True)

        # Create file in deepest level
        (deep_path / "test.txt").touch()

        # Test with max_depth=1
        dirs_depth_1 = self.manager.list_all_directories(max_depth=1)
        assert "level1" in dirs_depth_1
        # level2 and level3 should not be included as separate entries
        assert len([d for d in dirs_depth_1 if "level" in d]) == 1

        # Test with max_depth=2
        dirs_depth_2 = self.manager.list_all_directories(max_depth=2)
        assert "level1" in dirs_depth_2
        # Should include level1 and nested directories within it

        # Test with unlimited depth (default)
        dirs_unlimited = self.manager.list_all_directories()
        assert "level1" in dirs_unlimited

    def test_permission_error_handling(self):
        """Test handling of permission errors during directory listing."""
        from unittest.mock import patch

        # Mock iterdir to raise PermissionError
        with patch.object(Path, "iterdir") as mock_iterdir:
            mock_iterdir.side_effect = PermissionError("Access denied")

            with pytest.raises(PermissionError, match="Access denied"):
                self.manager.list_all_directories()

    def test_git_command_failure_in_list_changed_directories(self):
        """Test handling of git command failures in list_changed_directories."""
        with patch.object(self.manager, "_is_git_repository", return_value=True):
            with patch.object(self.manager, "_run_git_command") as mock_git:
                mock_git.side_effect = subprocess.CalledProcessError(1, "git")

                # The method should handle git errors gracefully and return empty list
                result = self.manager.list_changed_directories()
                assert result == []

    def test_determine_base_commit_fetch_failure(self):
        """Test determine_base_commit when fetch fails."""
        with patch.object(self.manager, "_run_git_command") as mock_git:
            # Mock successful first call but failing fetch
            def side_effect(cmd):
                if cmd[0] == "fetch":
                    raise subprocess.CalledProcessError(1, "git fetch")
                return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

            mock_git.side_effect = side_effect

            # Test push event scenario where fetch fails
            with patch.dict("os.environ", {"GITHUB_EVENT_NAME": "push"}):
                result = self.manager._determine_base_commit()
                assert result == "HEAD^"

    def test_find_git_directories_git_command_error(self) -> None:
        """Test list_changed_directories when git command fails."""
        import tempfile
        from unittest.mock import patch
        import subprocess

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a git repo structure
            repo_path = Path(temp_dir)
            (repo_path / ".git").mkdir()

            manager = DirectoryManager(base_path=str(repo_path))

            # Mock _run_git_command to raise CalledProcessError for the diff command
            with patch.object(manager, "_run_git_command") as mock_run_git:
                from unittest.mock import Mock
                
                # First call (for determining base commit) succeeds
                # Second call (for getting changed files) fails
                mock_run_git.side_effect = [
                    Mock(stdout="main\n", returncode=0),  # base commit determination
                    subprocess.CalledProcessError(
                        1, "git", "Git diff command failed"
                    ),  # diff command
                ]

                with pytest.raises(subprocess.CalledProcessError):
                    manager.list_changed_directories()
