"""Tests for Git utilities."""

from pathlib import Path
from unittest.mock import patch, Mock
from src.codeql_wrapper.infrastructure.git_utils import GitUtils, GitInfo


class TestGitUtils:
    """Test cases for Git utilities."""

    @patch("subprocess.run")
    def test_get_commit_sha_success(self, mock_run):
        """Test successful commit SHA extraction."""
        mock_run.return_value = Mock(returncode=0, stdout="abc123def456\n", stderr="")

        result = GitUtils._get_commit_sha(Path("/test"))

        assert result == "abc123def456"
        mock_run.assert_called_once_with(
            ["git", "rev-parse", "HEAD"],
            cwd=Path("/test"),
            capture_output=True,
            text=True,
            check=False,
        )

    @patch("subprocess.run")
    def test_get_commit_sha_failure(self, mock_run):
        """Test commit SHA extraction failure."""
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="Not a git repo")

        result = GitUtils._get_commit_sha(Path("/test"))

        assert result is None

    @patch("subprocess.run")
    def test_get_current_ref_branch(self, mock_run):
        """Test current ref extraction for branch."""
        mock_run.return_value = Mock(
            returncode=0, stdout="refs/heads/main\n", stderr=""
        )

        result = GitUtils._get_current_ref(Path("/test"))

        assert result == "refs/heads/main"

    @patch("subprocess.run")
    def test_get_current_ref_tag(self, mock_run):
        """Test current ref extraction for tag."""
        # First call (symbolic-ref) fails, second call (describe) succeeds
        mock_run.side_effect = [
            Mock(returncode=1, stdout="", stderr="not a symbolic ref"),
            Mock(returncode=0, stdout="v1.0.0\n", stderr=""),
        ]

        result = GitUtils._get_current_ref(Path("/test"))

        assert result == "refs/tags/v1.0.0"
        assert mock_run.call_count == 2

    @patch("subprocess.run")
    def test_get_remote_url_success(self, mock_run):
        """Test successful remote URL extraction."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="https://github.com/owner/repo.git\n",
            stderr="",
        )

        result = GitUtils._get_remote_url(Path("/test"))

        assert result == "https://github.com/owner/repo.git"

    def test_extract_repository_from_https_url(self):
        """Test repository extraction from HTTPS URL."""
        url = "https://github.com/owner/repo.git"
        result = GitUtils._extract_repository_from_url(url)
        assert result == "owner/repo"

    def test_extract_repository_from_ssh_url(self):
        """Test repository extraction from SSH URL."""
        url = "git@github.com:owner/repo.git"
        result = GitUtils._extract_repository_from_url(url)
        assert result == "owner/repo"

    def test_extract_repository_from_https_url_no_git_suffix(self):
        """Test repository extraction from HTTPS URL without .git suffix."""
        url = "https://github.com/owner/repo"
        result = GitUtils._extract_repository_from_url(url)
        assert result == "owner/repo"

    def test_extract_repository_invalid_url(self):
        """Test repository extraction from invalid URL."""
        url = "not-a-git-url"
        result = GitUtils._extract_repository_from_url(url)
        assert result is None

    def test_extract_repository_none_url(self):
        """Test repository extraction from None URL."""
        result = GitUtils._extract_repository_from_url(None)
        assert result is None

    @patch("subprocess.run")
    def test_is_git_repository_true(self, mock_run):
        """Test is_git_repository returns True for Git repo."""
        mock_run.return_value = Mock(returncode=0, stdout=".git\n", stderr="")

        result = GitUtils.is_git_repository(Path("/test"))

        assert result is True

    @patch("subprocess.run")
    def test_is_git_repository_false(self, mock_run):
        """Test is_git_repository returns False for non-Git directory."""
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="Not a git repo")

        result = GitUtils.is_git_repository(Path("/test"))

        assert result is False

    @patch.object(GitUtils, "_get_commit_sha")
    @patch.object(GitUtils, "_get_current_ref")
    @patch.object(GitUtils, "_get_remote_url")
    @patch.object(GitUtils, "_extract_repository_from_url")
    def test_get_git_info_complete(self, mock_extract, mock_remote, mock_ref, mock_sha):
        """Test complete Git info extraction."""
        mock_sha.return_value = "abc123"
        mock_ref.return_value = "refs/heads/main"
        mock_remote.return_value = "https://github.com/owner/repo.git"
        mock_extract.return_value = "owner/repo"

        result = GitUtils.get_git_info(Path("/test"))

        assert result.commit_sha == "abc123"
        assert result.ref == "refs/heads/main"
        assert result.remote_url == "https://github.com/owner/repo.git"
        assert result.repository == "owner/repo"

    @patch.object(GitUtils, "_get_commit_sha")
    @patch.object(GitUtils, "_get_current_ref")
    @patch.object(GitUtils, "_get_remote_url")
    def test_get_git_info_partial_failure(self, mock_remote, mock_ref, mock_sha):
        """Test Git info extraction with partial failures."""
        mock_sha.return_value = "abc123"
        mock_ref.side_effect = Exception("Git command failed")
        mock_remote.return_value = None

        result = GitUtils.get_git_info(Path("/test"))

        assert result.commit_sha == "abc123"
        assert result.ref is None
        assert result.remote_url is None
        assert result.repository is None

    def test_git_info_dataclass(self):
        """Test GitInfo dataclass creation."""
        git_info = GitInfo(
            repository="owner/repo",
            commit_sha="abc123",
            ref="refs/heads/main",
            remote_url="https://github.com/owner/repo.git",
        )

        assert git_info.repository == "owner/repo"
        assert git_info.commit_sha == "abc123"
        assert git_info.ref == "refs/heads/main"
        assert git_info.remote_url == "https://github.com/owner/repo.git"

    def test_git_info_dataclass_defaults(self) -> None:
        """Test GitInfo dataclass with default values."""
        git_info = GitInfo()

        assert git_info.repository is None
        assert git_info.commit_sha is None
        assert git_info.ref is None

    def test_get_git_info_with_invalid_path(self) -> None:
        """Test get_git_info handles invalid paths gracefully."""
        test_path = Path("/nonexistent/path")
        
        # Should return GitInfo with None values when path doesn't exist
        result = GitUtils.get_git_info(test_path)
        assert result.repository is None
        assert result.commit_sha is None
        assert result.ref is None

    def test_get_git_info_with_subprocess_exceptions(self) -> None:
        """Test get_git_info handles subprocess exceptions gracefully."""
        with patch("subprocess.run", side_effect=Exception("Subprocess error")):
            result = GitUtils.get_git_info(Path.cwd())
            assert result.repository is None
            assert result.commit_sha is None
            assert result.ref is None

    def test_is_git_repository_exception_handling(self) -> None:
        """Test is_git_repository handles exceptions gracefully."""
        test_path = Path("/nonexistent/path")

        # Should return False when path doesn't exist
        result = GitUtils.is_git_repository(test_path)
        assert result is False
