"""Use case for installing CodeQL CLI."""

import logging
from typing import Optional

from .....domain.entities.install_codeql_request import InstallCodeQLRequest
from .....domain.interfaces.codeql_service import CodeQLService, CodeQLInstallationInfo
from .....domain.exceptions.codeql_exceptions import CodeQLError, CodeQLInstallationError


class InstallCodeQLUseCase:
    """Use case for installing CodeQL CLI."""
    
    def __init__(self, codeql_service: CodeQLService, logger: Optional[logging.Logger] = None) -> None:
        """Initialize the use case with dependencies."""
        self._codeql_service = codeql_service
        self._logger = logger or logging.getLogger(__name__)
    
    async def execute(self, request: InstallCodeQLRequest) -> CodeQLInstallationInfo:
        """Execute the CodeQL installation process."""
        try:
            self._logger.info("Starting CodeQL installation process")
            
            # Check current installation status if not forcing reinstall
            if not request.force_reinstall:
                try:
                    current_info = await self._codeql_service.validate_installation()
                    
                    if current_info.is_installed:
                        if request.version:
                            # Check if specific version is already installed
                            if current_info.version == request.version:
                                self._logger.info(f"CodeQL version {request.version} is already installed")
                                return current_info
                            else:
                                self._logger.info(
                                    f"Different version installed ({current_info.version}), "
                                    f"installing requested version {request.version}"
                                )
                        else:
                            # Check if latest version is installed
                            if current_info.is_latest_version:
                                self._logger.info("Latest CodeQL version is already installed")
                                return current_info
                            else:
                                self._logger.info("Upgrading to latest CodeQL version")
                except CodeQLError:
                    # If validation fails, it likely means CodeQL is not installed
                    # Continue with installation
                    self._logger.info("CodeQL not found, proceeding with installation")
            
            # Perform installation
            self._logger.info(f"Installing CodeQL{f' version {request.version}' if request.version else ' (latest)'}")
            
            result = await self._codeql_service.install(
                version=request.version or "",
                force_reinstall=request.force_reinstall,
                persistent_path=request.persistent_path
            )
            
            self._logger.info(f"CodeQL installation completed successfully: {result.version}")
            return result
            
        except CodeQLInstallationError as e:
            self._logger.error(f"CodeQL installation failed: {e.message}")
            raise
        except CodeQLError as e:
            self._logger.error(f"CodeQL error during installation: {e.message}")
            raise
        except Exception as e:
            self._logger.error(f"Unexpected error during CodeQL installation: {str(e)}")
            raise CodeQLInstallationError(
                message=f"Installation failed due to unexpected error: {str(e)}",
                installation_path=request.installation_directory or "unknown"
            )
