"""Wrapper for CodeQL CLI operations with proper error handling and logging."""

import asyncio
import os
import shutil
import stat
from typing import List, Optional
from pathlib import Path

from ...domain.interfaces.codeql_service import CodeQLExecutionResult
from ...domain.exceptions.codeql_exceptions import CodeQLNotInstalledError, CodeQLExecutionError


class CodeQLCLI:
    """
    Wrapper for CodeQL CLI operations.
    
    Handles command execution, error handling, and result parsing
    for all CodeQL CLI interactions.
    """
    
    def __init__(self, executable_path: Optional[str] = None) -> None:
        """
        Initialize CodeQL CLI wrapper.
        
        Args:
            executable_path: Custom path to CodeQL executable (optional)
        """
        self._executable_path = executable_path or self._find_codeql_executable()
        
        if not self._executable_path:
            raise CodeQLNotInstalledError(
                "CodeQL CLI not found. Please install CodeQL or provide executable path."
            )
    
    async def execute_command(
        self,
        command_args: List[str],
        working_directory: Optional[str] = None,
        timeout_seconds: Optional[int] = None
    ) -> CodeQLExecutionResult:
        """
        Execute CodeQL command with specified arguments.
        
        Args:
            command_args: List of command arguments (excluding 'codeql')
            working_directory: Directory to execute command in
            timeout_seconds: Maximum execution time
            
        Returns:
            Execution result with output and metadata
            
        Raises:
            CodeQLExecutionError: If command execution fails
        """
        full_command = [self._executable_path] + command_args
        # Filter out None values to avoid subprocess errors
        filtered_command = [str(arg) for arg in full_command if arg is not None]
        command_str = " ".join(filtered_command)
        
        try:
            import time
            start_time = time.time()
            
            # Ensure executable has proper permissions on Unix-like systems
            await self._ensure_executable_permissions()
            
            # Execute command
            process = await asyncio.create_subprocess_exec(
                *filtered_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_directory
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise CodeQLExecutionError(
                    f"Command timed out after {timeout_seconds} seconds",
                    command=command_str,
                    stderr=""
                )
            
            execution_time = time.time() - start_time
            
            # Decode output
            stdout_text = stdout.decode('utf-8', errors='replace')
            stderr_text = stderr.decode('utf-8', errors='replace')
            
            return CodeQLExecutionResult(
                success=process.returncode == 0,
                exit_code=process.returncode if process.returncode is not None else -1,
                stdout=stdout_text,
                stderr=stderr_text,
                execution_time_seconds=execution_time,
                command_executed=command_str
            )
            
        except FileNotFoundError:
            raise CodeQLNotInstalledError(
                f"CodeQL executable not found: {self._executable_path}"
            )
        except PermissionError:
            raise CodeQLNotInstalledError(
                f"CodeQL executable is not executable: {self._executable_path}"
            )
        except Exception as e:
            raise CodeQLExecutionError(
                f"Failed to execute CodeQL command: {str(e)}",
                command=command_str,
                stderr=str(e)
            )
    
    def update_executable_path(self, new_path: str) -> None:
        """
        Update the path to CodeQL executable.
        
        Args:
            new_path: New path to CodeQL executable
            
        Raises:
            CodeQLNotInstalledError: If new path is invalid
        """
        if not Path(new_path).exists():
            raise CodeQLNotInstalledError(
                f"CodeQL executable not found at: {new_path}"
            )
        
        self._executable_path = new_path
    
    def get_executable_path(self) -> str:
        """Get current CodeQL executable path.

        Raises:
            CodeQLNotInstalledError: If the executable path is not set.
        """
        if self._executable_path is None:
            raise CodeQLNotInstalledError("CodeQL executable path is not set.")
        return self._executable_path
    
    def is_available(self) -> bool:
        """Check if CodeQL CLI is available and accessible."""
        return self._executable_path is not None and Path(self._executable_path).exists()
    
    async def _ensure_executable_permissions(self) -> None:
        """Ensure CodeQL executable has proper execution permissions."""
        import platform
        
        if platform.system().lower() != "windows":
            try:
                exe_path = Path(self.get_executable_path())
                current_mode = exe_path.stat().st_mode
                
                # Add execute permission if not present
                if not (current_mode & stat.S_IEXEC):
                    new_mode = current_mode | stat.S_IEXEC
                    exe_path.chmod(new_mode)
                    
            except (OSError, PermissionError):
                # If we can't set permissions, the execution will fail with a clearer error
                pass
    
    def _find_codeql_executable(self) -> Optional[str]:
        """Find CodeQL executable in system PATH or common locations."""
        # First, try system PATH
        codeql_path = shutil.which("codeql")
        if codeql_path:
            return codeql_path
        
        # Try common installation locations
        common_paths = [
            # macOS
            "/usr/local/bin/codeql",
            "/opt/homebrew/bin/codeql",
            # Linux
            "/usr/bin/codeql",
            "/usr/local/bin/codeql",
            # Windows
            "C:\\Program Files\\CodeQL\\bin\\codeql.exe",
            "C:\\Program Files (x86)\\CodeQL\\bin\\codeql.exe",
            # User installations
            os.path.expanduser("~/.codeql/bin/codeql"),
            os.path.expanduser("~/codeql/bin/codeql"),
            # Additional version-specific paths
            os.path.expanduser("~/.codeql/codeql-*/codeql/codeql"),
        ]
        
        for path in common_paths:
            if "*" in path:
                # Handle glob patterns for version-specific installations
                import glob
                matches = glob.glob(path)
                if matches:
                    # Use the first (likely most recent) match
                    sorted_matches = sorted(matches, reverse=True)
                    if Path(sorted_matches[0]).exists():
                        return sorted_matches[0]
            elif Path(path).exists():
                return path
        
        return None