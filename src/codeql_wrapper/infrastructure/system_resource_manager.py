"""System resource management infrastructure."""

import os
from typing import Any

# Try to import psutil, fallback gracefully if not available
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class SystemResourceManager:
    """Manages system resource detection and worker calculation."""

    def __init__(self, logger: Any) -> None:
        """Initialize the system resource manager."""
        self._logger = logger

    def get_available_memory_gb(self) -> float:
        """
        Get available system memory in GB.

        Returns the amount of memory that can be given instantly to processes
        without the system going into swap. This is more accurate for resource
        planning than total memory as it accounts for memory already in use.

        Returns:
            Available memory in GB. Falls back to 7GB if psutil is unavailable.
        """
        if not PSUTIL_AVAILABLE:
            self._logger.debug(
                "psutil not available, using conservative memory estimate"
            )
            return 7.0  # GitHub Actions standard runner

        try:
            return psutil.virtual_memory().available / (1024**3)
        except Exception as e:
            self._logger.debug(
                f"Failed to get memory info from psutil: {e}, "
                "using conservative memory estimate"
            )
            return 7.0  # Fallback to GitHub Actions standard runner

    def calculate_optimal_workers(self) -> int:
        """
        Calculate optimal number of workers based on system resources.

        Takes into account CPU cores and available memory to prevent
        resource exhaustion, especially important for GitHub Actions runners.

        Returns:
            Optimal number of worker processes for CodeQL analysis
        """
        try:
            # Get system specifications
            cpu_count = os.cpu_count() or 2
            memory_gb = self.get_available_memory_gb()

            # Conservative calculation for CodeQL analysis
            # Each CodeQL worker typically needs:
            # - 1+ CPU cores for optimal performance
            # - 2-4GB RAM for database creation and analysis

            # Calculate limits based on available resources
            max_by_cpu = min(cpu_count, 8)  # Cap at 8 for efficiency
            max_by_memory = max(
                1, int(memory_gb / 2.5)
            )  # 2.5GB per worker (conservative)

            # Take the minimum to avoid resource exhaustion
            # Also apply reasonable bounds: min 1, max 10
            optimal = max(1, min(max_by_cpu, max_by_memory, 10))

            self._logger.debug(
                f"Calculated optimal workers: {optimal} "
                f"(CPU: {cpu_count}, Memory: {memory_gb:.1f}GB, "
                f"Limits - CPU: {max_by_cpu}, Memory: {max_by_memory})"
            )

            return optimal

        except Exception as e:
            self._logger.warning(f"Failed to calculate optimal workers: {e}")
            return 4  # Safe fallback for most environments
