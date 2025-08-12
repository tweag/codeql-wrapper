"""Git service for handling Git operations in the v2 architecture."""

import os
import re
import subprocess
from pathlib import Path
from typing import List, Optional, Any
from dataclasses import dataclass

from git import Repo as GitRepo, GitCommandError as GitCmdError, InvalidGitRepositoryError as InvalidGitRepoError


@dataclass
class GitInfo:
    """Git repository information."""
    current_ref: str
    base_ref: Optional[str]
    repository: str
    commit_sha: Optional[str] = None
    remote_url: Optional[str] = None
    is_git_repository: Optional[bool] = None
    working_dir: Path = Path.cwd()


class GitService:
    """Service for Git operations using proven logic from existing git_utils.py."""
    
    DEFAULT_FALLBACK_BRANCHES = ["origin/main", "origin/master", "origin/develop"]
    GITHUB_AUTH_URL_FORMAT = "https://x-access-token:{token}@github.com/{owner}/{repo}"
    
    def __init__(self, repository_path: Path, logger):
        """Initialize Git service.
        
        Args:
            repository_path: Path to the Git repository
            logger: Logger instance
        """
        self.logger = logger
        self.repository_path = repository_path
        self.repo: Optional[Any] = None
        
        if GitRepo:
            try:
                self.repo = GitRepo(self.repository_path, search_parent_directories=True)
            except (InvalidGitRepoError, ImportError) as e:
                self.logger.warning(f"Could not initialize Git repository at {repository_path}: {e}")
        else:
            self.logger.info("GitPython not available, using subprocess fallback")
    
    def get_changed_files(self, base_ref: Optional[str], current_ref: Optional[str]) -> List[str]:
        """Get changed files between Git references using proven logic.
        
        This method is based on the existing get_diff_files method from git_utils.py
        but adapted to work with the v2 architecture.
        
        Args:
            base_ref: Base Git reference for comparison
            current_ref: Current Git reference (optional, defaults to HEAD)
            
        Returns:
            List of changed file paths
        """
        if not self.repo:
            self.logger.warning("No Git repository available, using subprocess fallback")
            return self._get_changed_files_subprocess(base_ref, current_ref)
        
        try: 
            # If no base_ref is provided, return empty list (analyze all files)
            if not base_ref:
                self.logger.debug(
                    "No base_ref provided - returning empty changed files list (will analyze all)"
                )
                return []
            
            self._fetch_repo()
            
            # Try to resolve the base ref, fallback to origin/ prefix if needed
            base_ref_to_use = base_ref
            try:
                base_ref_commit = self.repo.commit(base_ref_to_use)
            except Exception:
                base_ref_to_use = f"origin/{base_ref}"
                self.logger.debug(
                    f"Could not resolve '{base_ref}', trying '{base_ref_to_use}'"
                )
                base_ref_commit = self.repo.commit(base_ref_to_use)
            
            # Resolve current commit with fallback logic
            current_commit = None
            try:
                if not current_ref or current_ref == "HEAD" or current_ref.startswith("refs/pull"):
                    current_commit = self.repo.head.commit
                    self.logger.debug("Using HEAD for current commit")
                else:
                    # Try to resolve the current_ref directly first
                    try:
                        current_commit = self.repo.commit(current_ref)
                        self.logger.debug(f"Successfully resolved current ref: {current_ref}")
                    except Exception:
                        # If that fails, try alternative formats
                        if current_ref.startswith("refs/heads/"):
                            # Try as remote branch
                            remote_ref = current_ref.replace("refs/heads/", "origin/")
                            self.logger.debug(f"Trying remote ref: {remote_ref}")
                            current_commit = self.repo.commit(remote_ref)
            except Exception as e:
                self.logger.warning(f"Failed to resolve current commit, using HEAD: {e}")
                current_commit = self.repo.head.commit
            
            if not current_commit:
                raise Exception("Could not resolve current commit")
            
            # Get the diff from base_ref to current
            diff = base_ref_commit.diff(current_commit)
            
            changed_files = [item.a_path for item in diff if item.a_path is not None]
            self.logger.debug(
                f"Found {len(changed_files)} changed files between "
                f"{base_ref_to_use} and {current_commit.hexsha[:8]}"
            )
            return changed_files
            
        except Exception as e:
            self.logger.error(f"Failed to get diff files using GitPython: {e}")
            self.logger.warning("Falling back to subprocess method")
            return self._get_changed_files_subprocess(base_ref, current_ref)
    
    def _get_changed_files_subprocess(self, base_ref: Optional[str], current_ref: Optional[str]) -> List[str]:
        """Fallback method using subprocess when GitPython is not available or fails."""
        try:
            if not base_ref:
                return []
            
            # Build git diff command
            git_args = ["git", "diff", "--name-only"]
            
            # Add references
            if current_ref and current_ref != "HEAD":
                git_args.extend([base_ref, current_ref])
            else:
                git_args.extend([base_ref, "HEAD"])
            
            self.logger.debug(f"Running git command: {' '.join(git_args)}")
            
            # Get changed files using git diff
            result = subprocess.run(
                git_args,
                cwd=self.repository_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            changed_files = [f.strip() for f in result.stdout.split('\n') if f.strip()]
            self.logger.debug(f"Subprocess detected {len(changed_files)} changed files")
            return changed_files
            
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"Failed to detect changed files using git subprocess: {e}")
            return []
        except Exception as e:
            self.logger.warning(f"Error detecting changed files: {e}")
            return []
    
    def _fetch_repo(self, depth: int = 2) -> None:
        """Fetch the repository with optional depth and authentication."""
        if not self.repo:
            return
        
        origin = self.repo.remotes.origin
        original_url = origin.url
        
        try:
            self.logger.debug(f"Fetching repository with depth={depth}")
            
            # Setup GitHub authentication if token is available
            if os.getenv("GITHUB_TOKEN"):
                auth_url = self._setup_github_auth_url(original_url)
                origin.set_url(auth_url)
            
            origin.fetch(depth=depth)
            
        except GitCmdError as e:
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
            self.logger.warning("Could not parse URL for GitHub auth, using original URL")
            return origin_url
    
    def _parse_repository_url(self, url: str) -> tuple[str, str]:
        """Parse a Git repository URL to extract owner and repository name."""
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
