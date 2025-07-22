"""Git utilities for extracting repository information."""

import os
from pathlib import Path

from typing import Optional, List
from dataclasses import dataclass
from git import Repo

from .logger import get_logger


@dataclass
class GitInfo:
    """Git repository information."""

    current_ref: str  # Format: 'refs/heads/branch-name'
    base_ref: Optional[str]  # Format: 'refs/heads/branch-name' or None if not provided
    repository: str  # Format: 'owner/name'
    commit_sha: Optional[str] = None
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

    def get_git_info(
        self, base_ref: Optional[str] = None, current_ref: Optional[str] = None
    ) -> GitInfo:
        self.logger.debug(f"Getting Git info for repository: {self.repository_path}")

        # Get consistent commit SHA across CI platforms
        current_ref_resolved = self.get_git_ref(current_ref)
        commit_sha = self._get_consistent_commit_sha(current_ref_resolved)

        git_info = GitInfo(
            repository=self.repo.remotes.origin.url.split("/")[-2]
            + "/"
            + self.repo.remotes.origin.url.split("/")[-1].replace(".git", ""),
            commit_sha=commit_sha,
            current_ref=current_ref_resolved,
            base_ref=self.get_base_ref(base_ref),
            remote_url=self.repo.remotes.origin.url,
            is_git_repository=True,
            working_dir=Path(self.repo.working_dir),
        )

        self.logger.debug(f"Git info: {git_info}")
        self.logger.debug(f"  Is Git repository: {git_info.is_git_repository}")
        self.logger.debug(f"  Repository: {git_info.repository}")
        self.logger.debug(f"  Working dir: {self.repo.working_dir}")
        self.logger.debug(f"  Remote URL: {git_info.remote_url}")
        self.logger.debug(f"  Commit SHA: {git_info.commit_sha}")
        self.logger.debug(f"  Current Ref (--ref): {git_info.current_ref}")
        self.logger.debug(f"  Base ref (--base-ref): {git_info.base_ref}")

        return git_info

    def _get_consistent_commit_sha(self, current_ref: str) -> str:
        """
        Get a consistent commit SHA across different CI platforms.

        For pull request merge refs, try to get the actual PR head commit
        instead of the platform-specific merge commit.
        """
        try:
            # For pull request merge refs like 'refs/pull/27/merge'
            if current_ref.startswith("refs/pull/") and current_ref.endswith("/merge"):
                # Try to get the PR head commit (refs/pull/27/head)
                head_ref = current_ref.replace("/merge", "/head")
                try:
                    head_commit = self.repo.commit(head_ref)
                    self.logger.debug(
                        f"Using PR head commit for consistency: {head_commit.hexsha}"
                    )
                    return head_commit.hexsha
                except Exception as e:
                    self.logger.debug(
                        f"Could not resolve PR head ref '{head_ref}': {e}"
                    )

                # Fallback: try to get the second parent of the merge commit (the PR commit)
                try:
                    merge_commit = self.repo.head.commit
                    if len(merge_commit.parents) >= 2:
                        pr_commit = merge_commit.parents[
                            1
                        ]  # Second parent is usually the PR head
                        self.logger.debug(
                            f"Using PR commit from merge parents: {pr_commit.hexsha}"
                        )
                        return pr_commit.hexsha
                except Exception as e:
                    self.logger.debug(
                        f"Could not get PR commit from merge parents: {e}"
                    )

            # Default: use HEAD commit
            head_sha = self.repo.head.commit.hexsha
            self.logger.debug(f"Using HEAD commit: {head_sha}")
            return head_sha

        except Exception as e:
            self.logger.warning(f"Error getting consistent commit SHA: {e}")
            return self.repo.head.commit.hexsha

    def get_diff_files(self, git_info: GitInfo) -> List[str]:

        try:
            # If no base_ref is provided, return empty list (analyze all files)
            if not git_info.base_ref:
                self.logger.debug(
                    "No base_ref provided - returning empty changed files list (will analyze all)"
                )
                return []

            self.fetch_repo()

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
            if git_info.current_ref == "HEAD" or git_info.current_ref.startswith(
                "refs/pull"
            ):
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

    def fetch_repo(self, depth: int = 2) -> None:
        origin = self.repo.remotes.origin

        try:
            self.logger.info(f"Fetching repository with depth={depth}")
            if os.getenv("GITHUB_TOKEN"):
                origin.set_url(
                    (
                        f"https://x-access-token:{os.getenv('GITHUB_TOKEN')}"
                        f"@github.com/{origin.url.split('/')[-2]}/"
                        f"{origin.url.split('/')[-1]}"
                    )
                )

            origin.fetch(depth=depth)
        except Exception as e:
            self.logger.warning(f"Failed to fetch repository: {e}")

    def get_git_ref(self, current_ref: Optional[str]) -> str:
        ref = None
        if current_ref:
            self.logger.debug("Using provided current_ref")
            ref = current_ref
        elif os.getenv("GITHUB_REF"):
            self.logger.debug("Using GITHUB_REF environment variable")
            ref = os.getenv("GITHUB_REF")
        elif os.getenv("CI_COMMIT_REF_NAME"):
            self.logger.debug("Using CI_COMMIT_REF_NAME environment variable")
            ref = os.getenv("CI_COMMIT_REF_NAME")
        elif os.getenv("BITBUCKET_BRANCH"):
            self.logger.debug("Using BITBUCKET_BRANCH environment variable")
            ref = os.getenv("BITBUCKET_BRANCH")
        elif not self.repo.head.is_detached:
            self.logger.debug("Using repository metadata (Not Detached HEAD state)")
            ref = self.repo.head.ref.path

        if ref is None:
            raise Exception("No ref provided or found in environment variables")

        return ref

    def get_base_ref(self, base_ref: Optional[str] = None) -> Optional[str]:
        ref = None

        if base_ref:
            self.logger.debug("Using provided base_ref")
            ref = base_ref
        elif os.getenv("GITHUB_BASE_REF"):
            self.logger.debug("Using GITHUB_BASE_REF environment variable")
            ref = os.getenv("GITHUB_BASE_REF")
        elif os.getenv("CI_MERGE_REQUEST_TARGET_BRANCH_NAME"):
            self.logger.debug(
                "Using CI_MERGE_REQUEST_TARGET_BRANCH_NAME environment variable"
            )
            ref = os.getenv("CI_MERGE_REQUEST_TARGET_BRANCH_NAME")
        elif os.getenv("BITBUCKET_PR_DESTINATION_BRANCH"):
            self.logger.debug(
                "Using BITBUCKET_PR_DESTINATION_BRANCH environment variable"
            )
            ref = os.getenv("BITBUCKET_PR_DESTINATION_BRANCH")

        if ref is None:
            self.logger.debug(
                "No base_ref provided or found in environment variables - will analyze all files"
            )

        return ref
