"""Git utilities for extracting repository information."""
from pathlib import Path

# from turtle import st
from typing import Optional, List
from dataclasses import dataclass
from git import Repo

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

    def __init__(self, repository_path: Path):
        """Initialize GitUtils."""
        self.logger = get_logger(__name__)
        self.repository_path = repository_path
        self.repo = Repo(self.repository_path)

    def get_git_info(self, base_ref: Optional[str] = None) -> GitInfo:
        return GitInfo(
            repository=self.repo.remotes.origin.url.split("/")[-2]
            + "/"
            + self.repo.remotes.origin.url.split("/")[-1].replace(".git", ""),
            commit_sha=self.repo.head.commit.hexsha,
            current_ref=self.repo.head.ref.name,
            base_ref=base_ref or "main",
            remote_url=self.repo.remotes.origin.url,
            is_git_repository=True,
        )

    def is_pr(self, ref_name: str) -> bool:
        # Check if it's a local branch
        if ref_name in self.repo.branches:
            return False

        # Check if it's a remote PR (e.g., origin/pr/123)
        for ref in self.repo.remote().refs:
            if ref.name.endswith(ref_name):
                if "pull" in ref.name or "pr" in ref.name:
                    return True

        return False

    def get_diff_files(self) -> List[str]:
        git_info = self.get_git_info()
        # Get references to the branches
        base_ref_commit = self.repo.commit(git_info.base_ref)
        ref_commit = self.repo.commit(git_info.current_ref)

        # Get the diff from base_ref to ref
        diff = base_ref_commit.diff(ref_commit)

        return [item.a_path for item in diff if item.a_path is not None]
