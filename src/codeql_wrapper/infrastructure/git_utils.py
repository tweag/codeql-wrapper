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
    base_ref: str = "main"  # Default base branch
    remote_url: Optional[str] = None
    is_git_repository: Optional[bool] = None


class GitUtils:
    """Utility class for Git operations."""

    def __init__(self, repository_path: Path):
        """Initialize GitUtils."""
        self.logger = get_logger(__name__)
        self.repository_path = repository_path
        self.repo = Repo(self.repository_path, search_parent_directories=True)

    def get_git_info(self, base_ref: Optional[str] = None) -> GitInfo:
        git_info = GitInfo(
            repository=self.repo.remotes.origin.url.split("/")[-2]
            + "/"
            + self.repo.remotes.origin.url.split("/")[-1].replace(".git", ""),
            commit_sha=self.repo.head.commit.hexsha,
            current_ref=self.repo.head.ref.name,
            base_ref=base_ref or "main",
            remote_url=self.repo.remotes.origin.url,
            is_git_repository=True,
        )

        self.logger.debug(f"Git info: {git_info}")
        self.logger.debug(f"  Is Git repository: {git_info.is_git_repository}")
        self.logger.debug(f"  Repository: {git_info.repository}")
        self.logger.debug(f"  Current branch: {git_info.current_ref}")
        self.logger.debug(f"  Remote URL: {git_info.remote_url}")
        self.logger.debug(f"  Commit SHA: {git_info.commit_sha}")
        self.logger.debug(f"  Base ref: {git_info.base_ref}")

        return git_info

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

        self.fetch_repo(git_info.base_ref)

        # Get references to the branches
        base_ref_commit = self.repo.commit(git_info.base_ref)
        ref_commit = self.repo.commit(git_info.current_ref)

        # Get the diff from base_ref to ref
        diff = base_ref_commit.diff(ref_commit)

        return [item.a_path for item in diff if item.a_path is not None]

    def fetch_repo(self, base_ref: str, depth: int = 2) -> None:

        origin = self.repo.remotes.origin

        if self.is_pr(base_ref):
            self.logger.info(f"Fetching base branch of PR: {base_ref}")
            origin.fetch(refspec=base_ref, depth=depth)
        else:
            self.logger.info("Fetching default (non-PR) branch")
            origin.fetch(depth=depth)
