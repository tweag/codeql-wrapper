"""Git utilities for extracting repository information."""

import os
import re
import json
import urllib.request
from pathlib import Path
from typing import Optional, List, Tuple
from dataclasses import dataclass
from git import Repo, GitCommandError, InvalidGitRepositoryError

from .logger import get_logger


@dataclass
class GitInfo:
    """
    Git repository information.

    Attributes:
        current_ref: Current Git reference (e.g., 'refs/heads/branch-name')
        base_ref: Base reference for comparison (optional)
        repository: Repository identifier in 'owner/name' format
        commit_sha: SHA of the current commit
        remote_url: URL of the remote repository
        is_git_repository: Whether the directory is a Git repository
        working_dir: Path to the working directory
    """

    current_ref: str
    base_ref: Optional[str]
    repository: str
    commit_sha: Optional[str] = None
    remote_url: Optional[str] = None
    is_git_repository: Optional[bool] = None
    working_dir: Path = Path.cwd()


class GitUtils:
    """
    Utility class for Git operations.

    This class provides methods to extract Git repository information,
    handle different CI/CD environments, and perform Git operations
    like fetching and diff calculations.

    Attributes:
        DEFAULT_FALLBACK_BRANCHES: List of default branches to try as fallbacks
        GITHUB_AUTH_URL_FORMAT: Format string for GitHub authentication URLs
        PR_REF_PATTERN: Regex pattern for pull request references
    """

    # Default fallback branch names
    DEFAULT_FALLBACK_BRANCHES = ["origin/main", "origin/master", "origin/develop"]

    # GitHub token authorization header format
    GITHUB_AUTH_URL_FORMAT = "https://x-access-token:{token}@github.com/{owner}/{repo}"

    # Pull request ref pattern
    PR_REF_PATTERN = re.compile(r"refs/pull/(\d+)/(head|merge)")

    def __init__(self, repository_path: Path):
        """
        Initialize GitUtils.

        Args:
            repository_path: Path to the Git repository

        Raises:
            InvalidGitRepositoryError: If the path is not a valid Git repository
        """
        self.logger = get_logger(__name__)
        self.repository_path = repository_path
        try:
            self.repo = Repo(self.repository_path, search_parent_directories=True)
        except InvalidGitRepositoryError as e:
            self.logger.error(f"Invalid Git repository at {repository_path}: {e}")
            raise

    def _parse_repository_url(self, url: str) -> Tuple[str, str]:
        """
        Parse a Git repository URL to extract owner and repository name.

        Args:
            url: Repository URL (SSH or HTTPS format)

        Returns:
            Tuple of (owner, repository_name)

        Raises:
            ValueError: If URL format is not supported
        """
        # Handle SSH format: git@github.com:owner/repo.git
        if url.startswith("git@"):
            match = re.search(r"git@[^:]+:([^/]+)/(.+?)(?:\.git)?$", url)
            if match:
                return match.group(1), match.group(2)

        # Handle HTTPS format: https://github.com/owner/repo.git
        if url.startswith("https://"):
            match = re.search(r"https://[^/]+/([^/]+)/(.+?)(?:\.git)?$", url)
            if match:
                return match.group(1), match.group(2)

        # Fallback: try to extract from URL parts
        parts = url.rstrip("/").split("/")
        if len(parts) >= 2:
            repo_name = parts[-1].replace(".git", "")
            owner = parts[-2]
            # Validate extracted parts
            if re.match(r"^[a-zA-Z0-9._-]+$", owner) and re.match(
                r"^[a-zA-Z0-9._-]+$", repo_name
            ):
                return owner, repo_name

        raise ValueError(f"Unable to parse repository URL: {url}")

    def _get_repository_info(self) -> str:
        """Get repository information in 'owner/name' format."""
        try:
            origin_url = self.repo.remotes.origin.url
            owner, repo_name = self._parse_repository_url(origin_url)
            return f"{owner}/{repo_name}"
        except (ValueError, AttributeError) as e:
            self.logger.warning(f"Failed to parse repository URL: {e}")
            # Fallback to original method
            return (
                self.repo.remotes.origin.url.split("/")[-2]
                + "/"
                + self.repo.remotes.origin.url.split("/")[-1].replace(".git", "")
            )

    def _setup_github_auth_url(self, origin_url: str) -> str:
        """Setup GitHub URL with token authentication."""
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            return origin_url

        try:
            owner, repo_name = self._parse_repository_url(origin_url)
            return self.GITHUB_AUTH_URL_FORMAT.format(
                token=github_token, owner=owner, repo=repo_name
            )
        except ValueError:
            self.logger.warning(
                "Could not parse URL for GitHub auth, using original URL"
            )
            return origin_url

    def get_git_info(
        self, base_ref: Optional[str] = None, current_ref: Optional[str] = None
    ) -> GitInfo:
        self.logger.debug(f"Getting Git info for repository: {self.repository_path}")

        # Get consistent commit SHA using the fetch approach
        current_ref_resolved = self.get_git_ref(current_ref)
        commit_sha = self._get_consistent_commit_sha(current_ref_resolved)

        git_info = GitInfo(
            repository=self._get_repository_info(),
            commit_sha=commit_sha,
            current_ref=current_ref_resolved,
            base_ref=self.get_base_ref(base_ref, current_ref_resolved),
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
        Get a consistent commit SHA by fetching the ref and using FETCH_HEAD.

        Equivalent to:
        git fetch origin refs/pull/xx/merge
        git rev-parse FETCH_HEAD
        """
        try:
            # For PR merge refs, fetch the specific ref and use FETCH_HEAD
            if current_ref.startswith("refs/pull/"):
                self.logger.debug(f"Fetching specific ref: {current_ref}")

                # Get origin remote and set up authentication
                origin = self.repo.remotes.origin
                original_url = origin.url

                # Set up GitHub token authentication if available
                if os.getenv("GITHUB_TOKEN"):
                    self.logger.debug(
                        "Setting up GitHub token authentication for fetch"
                    )
                    auth_url = self._setup_github_auth_url(original_url)
                    origin.set_url(auth_url)

                try:
                    # Equivalent to: git fetch origin refs/pull/xx/merge
                    origin.fetch(current_ref)

                    # Equivalent to: git rev-parse FETCH_HEAD
                    fetch_head_commit = self.repo.commit("FETCH_HEAD")
                    commit_sha = fetch_head_commit.hexsha

                    self.logger.debug(f"Using FETCH_HEAD commit: {commit_sha}")
                    return commit_sha
                finally:
                    # Restore original URL
                    if os.getenv("GITHUB_TOKEN"):
                        origin.set_url(original_url)

        except Exception as e:
            self.logger.debug(f"Failed to fetch specific ref {current_ref}: {e}")

        # Fallback to HEAD commit for non-PR refs or if fetch fails
        commit_sha = self.repo.head.commit.hexsha
        self.logger.debug(f"Using HEAD commit: {commit_sha}")
        return commit_sha

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
            # Resolve current commit with fallback logic
            try:
                if git_info.current_ref == "HEAD" or git_info.current_ref.startswith(
                    "refs/pull"
                ):
                    current_commit = self.repo.head.commit
                    self.logger.debug("Using HEAD for current commit")
                else:
                    # Try to resolve the current_ref directly first
                    try:
                        current_commit = self.repo.commit(git_info.current_ref)
                        self.logger.debug(
                            f"Successfully resolved current ref: {git_info.current_ref}"
                        )
                    except Exception:
                        # If that fails, try alternative formats
                        if git_info.current_ref.startswith("refs/heads/"):
                            # Try as remote branch
                            remote_ref = git_info.current_ref.replace(
                                "refs/heads/", "origin/"
                            )
                            self.logger.debug(f"Trying remote ref: {remote_ref}")
                            current_commit = self.repo.commit(remote_ref)
            except Exception as e:
                self.logger.warning(
                    f"Failed to resolve current commit, using HEAD: {e}"
                )
                current_commit = self.repo.head.commit

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
        """Fetch the repository with optional depth and authentication."""
        origin = self.repo.remotes.origin
        original_url = origin.url

        try:
            self.logger.info(f"Fetching repository with depth={depth}")

            # Setup GitHub authentication if token is available
            if os.getenv("GITHUB_TOKEN"):
                auth_url = self._setup_github_auth_url(original_url)
                origin.set_url(auth_url)

            origin.fetch(depth=depth)

        except GitCommandError as e:
            self.logger.warning(f"Git fetch failed: {e}")
        except Exception as e:
            self.logger.warning(f"Failed to fetch repository: {e}")
        finally:
            # Restore original URL if we modified it
            if os.getenv("GITHUB_TOKEN"):
                try:
                    origin.set_url(original_url)
                except Exception as e:
                    self.logger.debug(f"Failed to restore original URL: {e}")

    def get_git_ref(self, current_ref: Optional[str]) -> str:
        """
        Get the current Git reference from various sources.

        Priority order:
        1. Provided current_ref parameter
        2. CI/CD environment variables
        3. Repository metadata (if not detached HEAD)

        Returns:
            The resolved Git reference

        Raises:
            Exception: If no ref can be determined
        """
        # Priority 1: Use provided current_ref
        if current_ref:
            self.logger.debug("Using provided current_ref")
            return current_ref

        # Priority 2: Check CI/CD environment variables
        ci_ref = self._get_ref_from_ci_environment()
        if ci_ref:
            return ci_ref

        # Priority 3: Use repository metadata (if not detached HEAD)
        if not self.repo.head.is_detached:
            self.logger.debug("Using repository metadata (Not Detached HEAD state)")
            return self.repo.head.ref.path

        raise Exception("No ref provided or found in environment variables")

    def _get_ref_from_ci_environment(self) -> Optional[str]:
        """Extract Git reference from CI/CD environment variables."""
        # GitHub Actions
        if os.getenv("GITHUB_REF"):
            self.logger.debug("Using GITHUB_REF environment variable")
            return os.getenv("GITHUB_REF")

        # CircleCI
        circle_pr_url = os.getenv("CIRCLE_PULL_REQUEST")
        if circle_pr_url:
            self.logger.debug("Using CIRCLE_PULL_REQUEST environment variable")
            pr_number = os.path.basename(circle_pr_url)
            ref = f"refs/pull/{pr_number}/merge"
            self.logger.debug(f"Constructed CircleCI PR ref: {ref}")
            return ref

        # Harness/Drone
        drone_pr = os.getenv("DRONE_PULL_REQUEST")
        if drone_pr:
            self.logger.debug("Using DRONE_PULL_REQUEST environment variable")
            ref = f"refs/pull/{drone_pr}/merge"
            self.logger.debug(f"Constructed Drone PR ref: {ref}")
            return ref

        # Azure Pipelines
        if os.getenv("BUILD_SOURCEBRANCH"):
            self.logger.debug("Using BUILD_SOURCEBRANCH environment variable")
            return os.getenv("BUILD_SOURCEBRANCH")

        return None

    def get_base_ref(
        self, base_ref: Optional[str] = None, current_ref: Optional[str] = None
    ) -> Optional[str]:
        """
        Get the base reference for comparison.

        Args:
            base_ref: Explicitly provided base reference
            current_ref: Current reference to help determine base

        Returns:
            The base reference or None
        """
        # Priority 1: Use provided base_ref
        if base_ref:
            self.logger.debug("Using provided base_ref")
            return base_ref

        # Priority 2: For pull requests, get target branch from CI environment
        if current_ref and current_ref.startswith("refs/pull/"):
            ci_base_ref = self._get_base_ref_from_ci_environment()
            if ci_base_ref:
                return ci_base_ref

        # Priority 3: For push events, use HEAD^
        self.logger.debug("Using HEAD^ as base_ref")
        return "HEAD^"

    def _get_base_ref_from_ci_environment(self) -> Optional[str]:
        """Extract base reference from CI/CD environment variables."""
        # GitHub Actions
        if os.getenv("GITHUB_BASE_REF"):
            self.logger.debug("Using GITHUB_BASE_REF environment variable")
            base_ref = os.getenv("GITHUB_BASE_REF")
            ref = f"origin/{base_ref}"
            self.logger.debug(f"base_ref: {ref}")
            return ref

        # CircleCI
        if os.getenv("CIRCLE_PULL_REQUEST"):
            self.logger.debug("Using CIRCLE_PULL_REQUEST for base ref")
            return self._get_circleci_base_ref()

        # Harness/Drone
        if os.getenv("DRONE_TARGET_BRANCH"):
            self.logger.debug("Using DRONE_TARGET_BRANCH environment variable")
            base_ref = os.getenv("DRONE_TARGET_BRANCH")
            ref = f"origin/{base_ref}"
            self.logger.debug(f"base_ref: {ref}")
            return ref

        # Azure Pipelines
        if os.getenv("SYSTEM_PULLREQUEST_TARGETBRANCHNAME"):
            self.logger.debug(
                "Using SYSTEM_PULLREQUEST_TARGETBRANCHNAME environment variable"
            )
            base_ref = os.getenv("SYSTEM_PULLREQUEST_TARGETBRANCHNAME")
            ref = f"origin/{base_ref}"
            self.logger.debug(f"base_ref: {ref}")
            return ref

        return None

    def _get_circleci_base_ref(self) -> str:
        """
        Get base ref for CircleCI pull requests using GitHub API.

        Returns:
            Base reference with origin/ prefix, or fallback branch
        """
        try:
            circle_pr_url = os.getenv("CIRCLE_PULL_REQUEST")
            if not circle_pr_url:
                return self._get_fallback_branch()

            # Extract PR number and repo path from URL
            pr_number = os.path.basename(circle_pr_url)

            # Extract repo path (owner/repo) from URL
            match = re.search(r"github\.com/([^/]+/[^/]+)/pull/\d+", circle_pr_url)
            if not match:
                self.logger.warning(
                    f"Could not extract repo path from: {circle_pr_url}"
                )
                return self._get_fallback_branch()

            repo_path = match.group(1)

            # Call GitHub API to get base ref
            github_token = os.getenv("GITHUB_TOKEN")
            if not github_token:
                self.logger.warning("No GITHUB_TOKEN found for CircleCI API call")
                return self._get_fallback_branch()

            api_url = f"https://api.github.com/repos/{repo_path}/pulls/{pr_number}"

            request = urllib.request.Request(api_url)
            request.add_header("Authorization", f"Bearer {github_token}")
            request.add_header("Accept", "application/vnd.github.v3+json")

            with urllib.request.urlopen(request, timeout=10) as response:
                if response.status != 200:
                    self.logger.warning(f"GitHub API returned status {response.status}")
                    return self._get_fallback_branch()

                data = json.loads(response.read().decode())
                base_ref = data.get("base", {}).get("ref")

                if base_ref:
                    ref = f"origin/{base_ref}"
                    self.logger.debug(f"CircleCI base ref from API: {ref}")
                    return ref
                else:
                    self.logger.warning(
                        "Could not get base ref from GitHub API response"
                    )
                    return self._get_fallback_branch()

        except urllib.error.HTTPError as e:
            self.logger.warning(f"GitHub API HTTP error: {e.code} - {e.reason}")
        except urllib.error.URLError as e:
            self.logger.warning(f"GitHub API URL error: {e.reason}")
        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse GitHub API response: {e}")
        except Exception as e:
            self.logger.warning(f"Failed to get CircleCI base ref from API: {e}")

        return self._get_fallback_branch()

    def _get_fallback_branch(self) -> str:
        """Get a fallback branch when base ref cannot be determined."""
        for branch in self.DEFAULT_FALLBACK_BRANCHES:
            if branch in self.repo.refs:
                self.logger.debug(f"Using fallback branch: {branch}")
                return branch

        # Ultimate fallback
        self.logger.warning("No fallback branches found, using origin/main")
        return "origin/main"
