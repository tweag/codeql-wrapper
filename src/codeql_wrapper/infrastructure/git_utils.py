"""Git utilities for extracting repository information."""

import subprocess
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass
from urllib.parse import urlparse

from .logger import get_logger


@dataclass
class GitInfo:
    """Git repository information."""

    repository: Optional[str] = None  # Format: 'owner/name'
    commit_sha: Optional[str] = None
    current_ref: Optional[str] = None  # Format: 'refs/heads/branch-name'
    base_ref: Optional[str] = None  # Base reference for comparisons
    remote_url: Optional[str] = None
    is_git_repository: Optional[bool] = None


class GitUtils:
    """Utility class for Git operations."""

    @staticmethod
    def get_git_info(
        repository_path: Optional[Path] = None,
        repository: Optional[str] = None,
        commit_sha: Optional[str] = None,
        current_ref: Optional[str] = None,
        base_ref: Optional[str] = None,
    ) -> GitInfo:
        """
        Extract Git information from a repository.

        Args:
            repository_path: Path to the Git repository

        Returns:
            GitInfo with extracted information
        """
        logger = get_logger(__name__)
        git_info = GitInfo()

        # If repository is provided, try to extract owner/name
        if repository:
            try:
                repository_owner, repository_name = repository.split("/", 1)
            except ValueError:
                logger.warning(
                    "Invalid repository format. Trying to extract from remote URL."
                )
                repository = None
        
        
        if repository_path is not None:
            git_info.commit_sha = commit_sha or GitUtils._get_commit_sha(repository_path)
            git_info.current_ref = current_ref or GitUtils._get_current_ref(repository_path)
            git_info.base_ref = base_ref

            git_info.remote_url = GitUtils._get_remote_url(repository_path)
            git_info.repository = repository or GitUtils._extract_repository_from_url(
                git_info.remote_url
            )
            git_info.is_git_repository = GitUtils.is_git_repository(repository_path)
        else:
            git_info.commit_sha = commit_sha
            git_info.current_ref = current_ref
            git_info.base_ref = base_ref
            git_info.remote_url = None
            git_info.repository = None
            git_info.is_git_repository = False

        logger.debug(f"Extracted Git info:")
        logger.debug(f"  Commit SHA: {git_info.commit_sha}")
        logger.debug(f"  Current Ref: {git_info.current_ref}")
        logger.debug(f"  Base Ref: {git_info.base_ref}")
        logger.debug(f"  Remote URL: {git_info.remote_url}")   
        logger.debug(f"  Repository: {git_info.repository}")   
        logger.debug(f"  Is Git Repository: {git_info.is_git_repository}")

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

    @staticmethod
    def get_diff_files(
        repository_path: Path,
        base_ref: str,
        target_ref: str,
        diff_filter: Optional[str] = None,
    ) -> List[str]:
        """
        Get list of files that differ between two Git references.

        Args:
            repository_path: Path to the Git repository
            base_ref: Base reference to compare from (default: HEAD~1)
            target_ref: Target reference to compare to (default: HEAD)
            diff_filter: Optional filter for diff types (A=added, M=modified, D=deleted, etc.)

        Returns:
            List of file paths that differ between the references
        """
        logger = get_logger(__name__)

        logger.debug(
            f"Getting diff files between {base_ref} and {target_ref} in {repository_path}"
        )

        # Build the git diff command
        cmd = ["git", "diff", "--name-only", f"{base_ref}..{target_ref}"]

        # Add filter if specified
        if diff_filter:
            cmd.insert(2, f"--diff-filter={diff_filter}")

        result = subprocess.run(
            cmd,
            cwd=repository_path,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            # Return list of file paths, filtering out empty lines
            return [line.strip() for line in result.stdout.split("\n") if line.strip()]
        else:
            # Log error but don't raise exception
            return []

    # Private methods
    @staticmethod
    def _get_commit_sha(repository_path: Path) -> Optional[str]:
        """Get the current commit SHA."""
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository_path,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()

    @staticmethod
    def _get_current_ref(repository_path: Path) -> Optional[str]:
        """Get the current Git reference."""

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

        return None

    @staticmethod
    def _get_remote_url(repository_path: Path) -> Optional[str]:
        """Get the remote URL for origin."""

        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=repository_path,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()

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
