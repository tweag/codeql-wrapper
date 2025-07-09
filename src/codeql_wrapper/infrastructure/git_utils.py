"""Git utilities for extracting repository information."""

import subprocess
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass
class GitInfo:
    """Git repository information."""

    repository: Optional[str] = None  # Format: 'owner/name'
    commit_sha: Optional[str] = None
    ref: Optional[str] = None  # Format: 'refs/heads/branch-name'
    remote_url: Optional[str] = None


class GitUtils:
    """Utility class for Git operations."""

    @staticmethod
    def get_git_info(repository_path: Path) -> GitInfo:
        """
        Extract Git information from a repository.

        Args:
            repository_path: Path to the Git repository

        Returns:
            GitInfo with extracted information
        """
        git_info = GitInfo()

        try:
            # Get current commit SHA
            git_info.commit_sha = GitUtils._get_commit_sha(repository_path)

            # Get current branch/ref
            git_info.ref = GitUtils._get_current_ref(repository_path)

            # Get remote URL and extract repository name
            remote_url = GitUtils._get_remote_url(repository_path)
            git_info.remote_url = remote_url
            git_info.repository = GitUtils._extract_repository_from_url(remote_url)

        except Exception:
            # If any Git operation fails, return partial information
            pass

        return git_info

    @staticmethod
    def is_git_repository(path: Path) -> bool:
        """Check if the given path is a Git repository."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=path,
                capture_output=True,
                text=True,
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False

    # Private methods
    @staticmethod
    def _get_commit_sha(repository_path: Path) -> Optional[str]:
        """Get the current commit SHA."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repository_path,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

    @staticmethod
    def _get_current_ref(repository_path: Path) -> Optional[str]:
        """Get the current Git reference."""
        try:
            # Try to get the symbolic ref (branch name)
            result = subprocess.run(
                ["git", "symbolic-ref", "HEAD"],
                cwd=repository_path,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                return result.stdout.strip()

            # If not on a branch, try to get tag
            result = subprocess.run(
                ["git", "describe", "--exact-match", "--tags", "HEAD"],
                cwd=repository_path,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                tag_name = result.stdout.strip()
                return f"refs/tags/{tag_name}"

            # If not on a tag either, we're in detached HEAD state
            # Return None so we use the default
            return None

        except Exception:
            pass
        return None

    @staticmethod
    def _get_remote_url(repository_path: Path) -> Optional[str]:
        """Get the remote URL for origin."""
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=repository_path,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

    @staticmethod
    def _extract_repository_from_url(remote_url: Optional[str]) -> Optional[str]:
        """
        Extract repository owner/name from Git remote URL.

        Supports both HTTPS and SSH URLs:
        - https://github.com/owner/repo.git
        - git@github.com:owner/repo.git
        """
        if not remote_url:
            return None

        try:
            # Remove .git suffix if present
            url = remote_url.rstrip("/")
            if url.endswith(".git"):
                url = url[:-4]

            # Handle SSH format: git@github.com:owner/repo
            if url.startswith("git@"):
                # Extract the part after the colon
                if ":" in url:
                    repo_part = url.split(":", 1)[1]
                    return repo_part
            else:
                # Parse the URL and validate the hostname
                parsed_url = urlparse(url)
                if parsed_url.hostname == "github.com":
                    # Extract the path component (e.g., /owner/repo)
                    repo_part = parsed_url.path.lstrip("/")
                    # Remove any query parameters or fragments
                    if "?" in repo_part:
                        repo_part = repo_part.split("?")[0]
                    if "#" in repo_part:
                        repo_part = repo_part.split("#")[0]
                    return repo_part

        except Exception:
            pass

        return None
