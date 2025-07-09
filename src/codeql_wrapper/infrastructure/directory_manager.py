"""Directory manager infrastructure module.

WARNING: This module is currently only used in tests and not in the main application.
It was designed for potential future use with monorepo directory detection but is not
currently integrated into the main codeql-wrapper functionality.
"""

import json
import subprocess
from pathlib import Path
from typing import List, Set, Union, Optional

from .logger import get_logger


class DirectoryManager:
    """Manages directory operations including listing and git-based change detection.

    WARNING: This class is currently only used in tests and not in the main application.
    """

    def __init__(self, base_path: Optional[Union[str, Path]] = None):
        """
        Initialize the directory manager.

        Args:
            base_path: Base directory to work from. Defaults to current
                working directory.
        """
        self.logger = get_logger(__name__)
        self.base_path = Path(base_path) if base_path else Path.cwd()

    def list_all_directories(
        self, exclude_hidden: bool = True, max_depth: int = 1
    ) -> List[str]:
        """
        List all top-level directories in the base path.

        Args:
            exclude_hidden: Whether to exclude directories starting with '.'
            max_depth: Maximum depth to search (1 for top-level only)

        Returns:
            List of directory names

        Raises:
            FileNotFoundError: If base path doesn't exist
            PermissionError: If base path is not accessible
        """
        if not self.base_path.exists():
            raise FileNotFoundError(f"Base path does not exist: {self.base_path}")

        if not self.base_path.is_dir():
            raise ValueError(f"Base path is not a directory: {self.base_path}")

        self.logger.info(f"Listing directories in: {self.base_path}")

        directories = []

        try:
            if max_depth == 1:
                # Only list immediate subdirectories
                for item in self.base_path.iterdir():
                    if item.is_dir():
                        dir_name = item.name
                        if not exclude_hidden or not dir_name.startswith("."):
                            directories.append(dir_name)
            else:
                # Use rglob for deeper searching
                for item in self.base_path.rglob("*"):
                    if item.is_dir():
                        # Calculate relative path and depth
                        rel_path = item.relative_to(self.base_path)
                        depth = len(rel_path.parts)

                        if depth <= max_depth:
                            dir_name = str(rel_path)
                            if not exclude_hidden or not any(
                                part.startswith(".") for part in rel_path.parts
                            ):
                                directories.append(dir_name)

        except PermissionError as e:
            self.logger.error(f"Permission denied accessing directory: {e}")
            raise

        directories.sort()
        self.logger.info(f"Found {len(directories)} directories")
        return directories

    def list_changed_directories(
        self,
        base_ref: Optional[str] = None,
        exclude_hidden: bool = True,
        github_event_name: Optional[str] = None,
        github_base_ref: Optional[str] = None,
    ) -> List[str]:
        """
        List top-level directories containing files that have changed according to git.

        Args:
            base_ref: Git reference to compare against (e.g., 'HEAD^', 'main')
            exclude_hidden: Whether to exclude directories starting with '.'
            github_event_name: GitHub event name (e.g., 'pull_request', 'push')
            github_base_ref: GitHub base branch reference for pull requests

        Returns:
            List of directory names containing changed files

        Raises:
            subprocess.CalledProcessError: If git commands fail
            FileNotFoundError: If not in a git repository
        """
        if not self._is_git_repository():
            raise FileNotFoundError("Not in a git repository")

        # Determine the base commit to compare against
        if base_ref is None:
            base_ref = self._determine_base_commit(github_event_name, github_base_ref)

        self.logger.info(f"Detecting changed directories against: {base_ref}")

        try:
            # Get list of changed files
            changed_files = self._get_changed_files(base_ref)

            # Extract top-level directories from changed files
            changed_dirs: Set[str] = set()

            for file_path in changed_files:
                if file_path:
                    # Get top-level directory (before first '/')
                    path_parts = Path(file_path).parts
                    if path_parts:
                        top_dir = path_parts[0]

                        # Only add if it's actually a directory (not a root-level file)
                        # Check if the file path contains a directory separator
                        if "/" in file_path or len(path_parts) > 1:
                            # Add if it doesn't start with '.' (when
                            # exclude_hidden is True)
                            if not exclude_hidden or not top_dir.startswith("."):
                                changed_dirs.add(top_dir)

            result = sorted(list(changed_dirs))
            self.logger.info(f"Found {len(result)} directories with changes: {result}")
            return result

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Git command failed: {e}")
            raise

    def to_json_array(self, directories: List[str]) -> str:
        """
        Convert a list of directories to a JSON array string.

        Args:
            directories: List of directory names

        Returns:
            JSON array string representation
        """
        return json.dumps(directories)

    def _is_git_repository(self) -> bool:
        """
        Check if the current directory is in a git repository.

        Returns:
            True if in a git repository, False otherwise
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.base_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _determine_base_commit(
        self,
        github_event_name: Optional[str] = None,
        github_base_ref: Optional[str] = None,
    ) -> str:
        """
        Determine the base commit to compare against based on context.

        Args:
            github_event_name: GitHub event name
            github_base_ref: GitHub base branch reference

        Returns:
            Git reference string
        """
        if github_event_name == "pull_request" and github_base_ref:
            # For pull requests, fetch and compare against the base branch
            try:
                self._run_git_command(["fetch", "origin", github_base_ref, "--depth=2"])
                return f"origin/{github_base_ref}"
            except subprocess.CalledProcessError:
                self.logger.warning(
                    f"Could not fetch {github_base_ref}, falling back to HEAD^"
                )
                return "HEAD^"
        else:
            # For push events or fallback, use HEAD^
            try:
                self._run_git_command(["fetch", "origin", "--depth=2"])
            except subprocess.CalledProcessError:
                self.logger.warning("Could not fetch from origin")
            return "HEAD^"

    def _get_changed_files(self, base_ref: str) -> List[str]:
        """
        Get list of changed files using git diff.

        Args:
            base_ref: Git reference to compare against

        Returns:
            List of changed file paths
        """
        try:
            result = self._run_git_command(["diff", base_ref, "HEAD", "--name-only"])

            # Filter out empty lines
            changed_files = [
                line.strip() for line in result.stdout.splitlines() if line.strip()
            ]
            return changed_files

        except subprocess.CalledProcessError:
            # If git diff fails, return empty list
            self.logger.warning(
                f"Could not get diff for {base_ref}, returning empty list"
            )
            return []

    def _run_git_command(self, args: List[str]) -> subprocess.CompletedProcess:
        """
        Run a git command in the base directory.

        Args:
            args: Git command arguments

        Returns:
            Completed process result

        Raises:
            subprocess.CalledProcessError: If git command fails
        """
        cmd = ["git"] + args
        self.logger.debug(f"Running git command: {' '.join(cmd)}")

        return subprocess.run(
            cmd, cwd=self.base_path, capture_output=True, text=True, check=True
        )

    def get_directory_info(self, include_changed: bool = False) -> dict:
        """
        Get comprehensive directory information.

        Args:
            include_changed: Whether to include git change information

        Returns:
            Dictionary with directory information
        """
        info = {
            "base_path": str(self.base_path),
            "all_directories": self.list_all_directories(),
            "is_git_repository": self._is_git_repository(),
        }

        if include_changed and info["is_git_repository"]:
            try:
                info["changed_directories"] = self.list_changed_directories()
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                self.logger.warning(f"Could not get changed directories: {e}")
                info["changed_directories"] = []

        return info
