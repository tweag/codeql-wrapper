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
    working_dir: Path = Path.cwd()


class GitUtils:
    """Utility class for Git operations."""

    def __init__(self, repository_path: Path):
        """Initialize GitUtils."""
        self.logger = get_logger(__name__)
        self.repository_path = repository_path
        self.repo = Repo(self.repository_path, search_parent_directories=True)

    def get_git_info(self, base_ref: Optional[str] = None) -> GitInfo:
        self.logger.debug(f"Getting Git info for repository: {self.repository_path}")

        git_info = GitInfo(
            repository=self.repo.remotes.origin.url.split("/")[-2]
            + "/"
            + self.repo.remotes.origin.url.split("/")[-1].replace(".git", ""),
            commit_sha=self.repo.head.commit.hexsha,
            current_ref=(
                self.repo.head.ref.name
                if not self.repo.head.is_detached
                else self.repo.head.name
            ),
            base_ref=base_ref or "main",
            remote_url=self.repo.remotes.origin.url,
            is_git_repository=True,
            working_dir=Path(self.repo.working_dir),
        )

        self.logger.debug(f"Git info: {git_info}")
        self.logger.debug(f"  Is Git repository: {git_info.is_git_repository}")
        self.logger.debug(f"  Repository: {git_info.repository}")
        self.logger.debug(f"  Current branch: {git_info.current_ref}")
        self.logger.debug(f"  Remote URL: {git_info.remote_url}")
        self.logger.debug(f"  Commit SHA: {git_info.commit_sha}")
        self.logger.debug(f"  Base ref: {git_info.base_ref}")
        self.logger.debug(f"  Working dir: {self.repo.working_dir}")

        return git_info

    def is_pr(self, ref_name: str) -> bool:
        head_commit = self.repo.head.commit

        # Look for remote PR refs that match HEAD commit
        for ref in self.repo.remote().refs:
            self.logger.debug(f"Checking remote ref: {ref.name} -> {ref.commit.hexsha}")
            if ref.commit == head_commit and ("pull" in ref.name or "pr" in ref.name):
                self.logger.debug(f"Matched PR ref: {ref.name}")
                return True

        return False

    def get_diff_files(self) -> List[str]:
        git_info = self.get_git_info()

        try:
            self.fetch_repo(git_info.base_ref, git_info.current_ref)

            # Try to resolve the base ref, fallback to origin/ prefix if needed
            base_ref_to_use = git_info.base_ref
            try:
                base_ref_commit = self.repo.commit(base_ref_to_use)
            except Exception:
                base_ref_to_use = f"origin/{git_info.base_ref}"
                self.logger.debug(
                    f"Could not resolve '{git_info.base_ref}', trying '{base_ref_to_use}'"
                )
                base_ref_commit = self.repo.commit(base_ref_to_use)

            # Use HEAD for current commit in detached HEAD state
            if git_info.current_ref == "HEAD":
                current_commit = self.repo.head.commit
            else:
                current_commit = self.repo.commit(git_info.current_ref)

            # Get the diff from base_ref to current
            diff = base_ref_commit.diff(current_commit)

            changed_files = [item.a_path for item in diff if item.a_path is not None]
            self.logger.debug(
                f"Found {len(changed_files)} changed files between "
                f"{base_ref_to_use} and {git_info.current_ref}"
            )
            return changed_files

        except Exception as e:
            self.logger.error(f"Failed to get diff files: {e}")
            self.logger.warning(
                "Falling back to analyzing all projects due to git diff failure"
            )
            return []

    def fetch_repo(
        self, base_ref: str, current_ref: Optional[str] = None, depth: int = 2
    ) -> None:
        origin = self.repo.remotes.origin

        try:
            self.logger.info(f"Fetching repository with depth={depth}")
            origin.fetch(depth=depth)
        except Exception as e:
            self.logger.warning(f"Failed to fetch repository: {e}")
