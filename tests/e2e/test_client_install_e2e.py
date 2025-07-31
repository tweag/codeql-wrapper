"""Client-side end-to-end tests for CodeQL CLI installation."""

import os
import platform
import subprocess
import sys
import tempfile
import pytest
from pathlib import Path
from typing import List, Optional, Dict, Any
import json


class TestCodeQLInstallClientE2E:
    """Test CodeQL installation as a real client would use it."""
    
    @pytest.fixture
    def temp_install_dir(self):
        """Create a temporary installation directory."""
        with tempfile.TemporaryDirectory(prefix="codeql_client_test_") as temp_dir:
            yield temp_dir
    
    def _run_cli_command(self, args: List[str], env: Optional[Dict[str, str]] = None) -> subprocess.CompletedProcess:
        """Run a CLI command and return the result."""
        # Use poetry run to execute the command in the virtual environment
        cmd = ["poetry", "run", "codeql-wrapper-v2"] + args
        
        # Set up environment
        test_env = os.environ.copy()
        if env:
            test_env.update(env)
        
        # Run the command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=test_env,
            timeout=300,  # 5 minutes timeout
            cwd="/Volumes/Mateus/Github/GHAS-Training/codeql-wrapper"
        )
        
        return result
    
    def _check_codeql_installed(self, install_dir: str) -> bool:
        """Check if CodeQL is properly installed in the given directory."""
        # CodeQL is installed in install_dir/codeql/codeql (or codeql.exe on Windows)
        codeql_path = Path(install_dir) / "codeql" / "codeql"
        if platform.system().lower() == "windows":
            codeql_path = Path(install_dir) / "codeql" / "codeql.exe"
        
        return codeql_path.exists() and codeql_path.is_file()
    
    def _get_codeql_version_from_binary(self, install_dir: str) -> Optional[str]:
        """Get the installed CodeQL version by running the binary."""
        # CodeQL is typically installed in install_dir/codeql/codeql
        codeql_path = Path(install_dir) / "codeql" / "codeql"
        if platform.system().lower() == "windows":
            codeql_path = Path(install_dir) / "codeql" / "codeql.exe"
        
        if not codeql_path.exists():
            return None
        
        try:
            result = subprocess.run(
                [str(codeql_path), "--version"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                # Parse version from output like "CodeQL command-line toolchain release 2.15.0"
                output_lines = result.stdout.strip().split('\n')
                for line in output_lines:
                    if 'release' in line.lower():
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part == 'release' and i + 1 < len(parts):
                                return parts[i + 1]
                # Fallback: return first line if no 'release' found
                return output_lines[0] if output_lines else "unknown"
        except Exception as e:
            print(f"Error getting CodeQL version: {e}")
            pass
        
        return None
    
    @pytest.mark.slow
    def test_client_install_latest_version(self, temp_install_dir: str):
        """Test installing latest version as a client would."""
        # Arrange
        args = [
            "install",
            "--installation-dir", temp_install_dir,
            "--no-persistent-path",  # Don't modify PATH in tests
            "--format", "json",
            "--quiet"
        ]
        
        # Act
        result = self._run_cli_command(args)
        
        # Assert
        assert result.returncode == 0, f"Installation should succeed. stderr: {result.stderr}, stdout: {result.stdout}"
        
        # Parse JSON output
        try:
            output = json.loads(result.stdout.strip())
            assert output["status"] == "success", f"Status should be success: {output}"
            assert "installation" in output, f"Should have installation info: {output}"
        except json.JSONDecodeError as e:
            pytest.fail(f"Output should be valid JSON: {result.stdout}, Error: {e}")
        
        # Verify actual installation
        assert self._check_codeql_installed(temp_install_dir), "CodeQL binary should be installed"
        
        # Verify binary works
        version = self._get_codeql_version_from_binary(temp_install_dir)
        # Just verify that we have a functional installation
        assert version is not None, "Should be able to get CodeQL version from installed binary"
    
    @pytest.mark.slow
    def test_client_install_specific_version(self, temp_install_dir: str):
        """Test installing a specific version as a client would."""
        # Arrange
        print(f"Installing CodeQL to: {temp_install_dir}")
        target_version = "2.15.0"
        args = [
            "install",
            "--version", target_version,
            "--installation-dir", temp_install_dir,
            "--no-persistent-path",
            "--format", "json",
            "--quiet"
        ]
        
        # Act
        result = self._run_cli_command(args)
        
        # Assert
        assert result.returncode == 0, f"Installation should succeed. stderr: {result.stderr}, stdout: {result.stdout}"
        
        # Parse JSON output
        try:
            output = json.loads(result.stdout.strip())
            assert output["status"] == "success", f"Status should be success: {output}"
            installation_info = output.get("installation", {})
            assert "installation_path" in installation_info, f"Should have installation path: {output}"
        except json.JSONDecodeError as e:
            pytest.fail(f"Output should be valid JSON: {result.stdout}, Error: {e}")
        
        # Verify actual installation
        assert self._check_codeql_installed(temp_install_dir), "CodeQL binary should be installed"
        
        # Verify correct version by running the binary directly
        installed_version = self._get_codeql_version_from_binary(temp_install_dir)
        assert installed_version is not None, "Should be able to get CodeQL version from installed binary"
        assert installed_version != "unknown", f"Version detection should work, got: {installed_version}"
        assert installed_version.startswith(target_version), f"Should install version {target_version}, got {installed_version}"
    
    @pytest.mark.slow
    def test_client_force_reinstall(self, temp_install_dir: str):
        """Test forcing reinstallation as a client would."""
        # First install
        target_version = "2.15.0"
        initial_args = [
            "install",
            "--version", target_version,
            "--installation-dir", temp_install_dir,
            "--no-persistent-path",
            "--format", "json",
            "--quiet"
        ]
        
        result = self._run_cli_command(initial_args)
        assert result.returncode == 0, f"Initial installation should succeed: {result.stderr}"
        
        # Verify first installation
        assert self._check_codeql_installed(temp_install_dir), "CodeQL should be installed after first run"
        first_version = self._get_codeql_version_from_binary(temp_install_dir)
        assert first_version is not None, "Should be able to get version after first install"
        
        # Force reinstall
        force_args = [
            "install",
            "--version", target_version,
            "--force",  # Force reinstall
            "--installation-dir", temp_install_dir,
            "--no-persistent-path",
            "--format", "json",
            "--quiet"
        ]
        
        result = self._run_cli_command(force_args)
        assert result.returncode == 0, f"Force reinstall should succeed: {result.stderr}"
        
        # Verify reinstallation
        assert self._check_codeql_installed(temp_install_dir), "CodeQL should still be installed"
        
        # Verify version is still correct
        second_version = self._get_codeql_version_from_binary(temp_install_dir)
        assert second_version == first_version, "Version should be the same after force reinstall"
    
    @pytest.mark.slow
    @pytest.mark.skipif(platform.system().lower() != "darwin", reason="macOS-specific test")
    def test_client_path_persistence_macos(self, temp_install_dir: str):
        """Test PATH persistence on macOS as a client would."""
        # Arrange
        args = [
            "install",
            "--version", "2.15.0",
            "--installation-dir", temp_install_dir,
            # Note: not using --no-persistent-path to test persistence
            "--format", "json",
            "--quiet"
        ]
        
        # Act
        result = self._run_cli_command(args)
        
        # Assert
        assert result.returncode == 0, f"Installation should succeed: {result.stderr}"
        
        # Verify installation
        assert self._check_codeql_installed(temp_install_dir), "CodeQL should be installed"
        
        # Check if PATH was modified in shell profiles
        home_dir = Path.home()
        shell_profiles = [
            home_dir / ".zshrc",
            home_dir / ".bash_profile",
            home_dir / ".bashrc"
        ]
        
        path_found = False
        updated_file = None
        
        for profile in shell_profiles:
            if profile.exists():
                content = profile.read_text()
                # Look for the CodeQL installation in the PATH
                if temp_install_dir in content:
                    path_found = True
                    updated_file = str(profile)
                    break
        
        assert path_found, f"Installation directory should be in a shell profile. Checked: {[str(p) for p in shell_profiles if p.exists()]}"
    
    def test_client_help_command(self):
        """Test that help command works as a client would expect."""
        # Test main help
        result = self._run_cli_command(["--help"])
        assert result.returncode == 0, "Help command should work"
        assert "CodeQL CLI management commands" in result.stdout, "Help should show description"
        
        # Test install help
        result = self._run_cli_command(["install", "--help"])
        assert result.returncode == 0, "Install help command should work"
        assert "Install CodeQL CLI" in result.stdout, "Install help should show description"
        assert "--version" in result.stdout, "Should show version option"
        assert "--force" in result.stdout, "Should show force option"
    
    def test_client_invalid_version(self, temp_install_dir: str):
        """Test client behavior with invalid version."""
        # Arrange
        args = [
            "install",
            "--version", "99.99.99",  # Invalid version
            "--installation-dir", temp_install_dir,
            "--no-persistent-path",
            "--format", "json",
            "--quiet"
        ]
        
        # Act
        result = self._run_cli_command(args)
        
        # Assert
        assert result.returncode != 0, "Invalid version should fail"
        
        # Check that error is properly formatted
        if result.stdout.strip():
            try:
                output = json.loads(result.stdout.strip())
                assert output["status"] == "error", "Status should be error"
                assert "message" in output, "Should have error message"
            except json.JSONDecodeError:
                # If not JSON, that's also acceptable for error output
                pass
    
    def test_client_with_github_token(self, temp_install_dir: str):
        """Test client usage with GitHub token."""
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            pytest.skip("GITHUB_TOKEN environment variable not set")
        
        # Arrange
        args = [
            "install",
            "--version", "2.15.0",
            "--installation-dir", temp_install_dir,
            "--no-persistent-path",
            "--github-token", github_token,
            "--format", "json",
            "--quiet"
        ]
        
        # Act
        result = self._run_cli_command(args)
        
        # Assert
        assert result.returncode == 0, f"Installation with token should succeed: {result.stderr}"
        assert self._check_codeql_installed(temp_install_dir), "CodeQL should be installed"
    
    def test_client_human_readable_output(self, temp_install_dir: str):
        """Test client with human-readable output format."""
        # Arrange
        args = [
            "install",
            "--version", "2.15.0",
            "--installation-dir", temp_install_dir,
            "--no-persistent-path",
            "--format", "human",  # Human-readable format
            "--verbose"  # Verbose output
        ]
        
        # Act
        result = self._run_cli_command(args)
        
        # Assert
        assert result.returncode == 0, f"Installation should succeed: {result.stderr}"
        assert "successfully" in result.stdout.lower(), "Should show success message"
        assert self._check_codeql_installed(temp_install_dir), "CodeQL should be installed"
    
    @pytest.mark.slow
    def test_client_install_without_installation_dir(self):
        """Test installing without specifying --installation-dir (uses default location)."""
        # Arrange
        args = [
            "install",
            "--version", "2.15.0",
            "--no-persistent-path",  # Don't modify PATH in tests
            "--format", "json",
            "--quiet"
        ]
        
        # Act
        result = self._run_cli_command(args)
        
        # Assert
        assert result.returncode == 0, f"Installation should succeed. stderr: {result.stderr}, stdout: {result.stdout}"
        
        # Parse JSON output
        try:
            output = json.loads(result.stdout.strip())
            assert output["status"] == "success", f"Status should be success: {output}"
            installation_info = output.get("installation", {})
            assert "installation_path" in installation_info, f"Should have installation path: {output}"
            
            # Verify that a default installation path was used
            installation_path = installation_info["installation_path"]
            assert installation_path is not None, "Should have a default installation path"
            assert len(installation_path) > 0, "Installation path should not be empty"
            
            # The CLI returns the full path to the binary, so we need to extract the base directory
            # installation_path is like "/path/to/codeql/codeql", we need "/path/to/"
            from pathlib import Path
            base_install_dir = str(Path(installation_path).parent.parent)
            
            # Check that CodeQL was actually installed
            assert self._check_codeql_installed(base_install_dir), f"CodeQL should be installed at {base_install_dir}"
            
            # Verify version using the base directory
            installed_version = self._get_codeql_version_from_binary(base_install_dir)
            assert installed_version is not None, "Should be able to get version from default installation"
            assert installed_version.startswith("2.15.0"), f"Should install correct version, got: {installed_version}"
            
        except json.JSONDecodeError as e:
            pytest.fail(f"Output should be valid JSON: {result.stdout}, Error: {e}")


if __name__ == "__main__":
    # Run tests with pytest
    import subprocess
    import sys
    
    result = subprocess.run([
        sys.executable, "-m", "pytest", __file__, "-v", "-s", "--tb=short"
    ], cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    
    sys.exit(result.returncode)
