"""Tests for system resource manager."""

import logging
import unittest
from unittest.mock import patch, MagicMock

from src.codeql_wrapper.infrastructure.system_resource_manager import (
    SystemResourceManager,
)


class TestSystemResourceManager(unittest.TestCase):
    """Test cases for SystemResourceManager."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.logger = logging.getLogger("test")
        self.manager = SystemResourceManager(self.logger)

    def test_get_available_memory_gb_with_psutil(self) -> None:
        """Test memory detection with psutil available."""
        with patch(
            "src.codeql_wrapper.infrastructure.system_resource_manager.PSUTIL_AVAILABLE",
            True,
        ):
            with patch(
                "src.codeql_wrapper.infrastructure.system_resource_manager.psutil"
            ) as mock_psutil:
                # Mock psutil to return 16GB available (16 * 1024^3 bytes)
                mock_memory = MagicMock()
                mock_memory.available = 16 * (1024**3)
                mock_psutil.virtual_memory.return_value = mock_memory

                result = self.manager.get_available_memory_gb()
                self.assertEqual(result, 16.0)

    def test_get_available_memory_gb_without_psutil(self) -> None:
        """Test memory detection fallback when psutil unavailable."""
        with patch(
            "src.codeql_wrapper.infrastructure.system_resource_manager.PSUTIL_AVAILABLE",
            False,
        ):
            result = self.manager.get_available_memory_gb()
            self.assertEqual(result, 7.0)  # Fallback value

    def test_get_available_memory_gb_with_psutil_error(self) -> None:
        """Test memory detection fallback when psutil raises exception."""
        with patch(
            "src.codeql_wrapper.infrastructure.system_resource_manager.PSUTIL_AVAILABLE",
            True,
        ):
            with patch(
                "src.codeql_wrapper.infrastructure.system_resource_manager.psutil"
            ) as mock_psutil:
                mock_psutil.virtual_memory.side_effect = Exception("Test error")

                result = self.manager.get_available_memory_gb()
                self.assertEqual(result, 7.0)  # Fallback value

    def test_calculate_optimal_workers_normal_system(self) -> None:
        """Test worker calculation for a normal system."""
        with patch("os.cpu_count", return_value=8):
            with patch.object(
                self.manager, "get_available_memory_gb", return_value=16.0
            ):
                result = self.manager.calculate_optimal_workers()
                # With 8 CPUs and 16GB RAM: min(8, 6) = 6 workers (capped at 6)
                self.assertEqual(result, 6)

    def test_calculate_optimal_workers_memory_limited(self) -> None:
        """Test worker calculation when memory is the limiting factor."""
        with patch("os.cpu_count", return_value=16):
            with patch.object(
                self.manager, "get_available_memory_gb", return_value=4.0
            ):
                result = self.manager.calculate_optimal_workers()
                # With 16 CPUs and 4GB RAM: min(8, 1) = 1 worker (memory limited)
                self.assertEqual(result, 1)

    def test_calculate_optimal_workers_cpu_limited(self) -> None:
        """Test worker calculation when CPU is the limiting factor."""
        with patch("os.cpu_count", return_value=2):
            with patch.object(
                self.manager, "get_available_memory_gb", return_value=32.0
            ):
                result = self.manager.calculate_optimal_workers()
                # With 2 CPUs and 32GB RAM: min(2, 12) = 2 workers (CPU limited)
                self.assertEqual(result, 2)

    def test_calculate_optimal_workers_minimum_bound(self) -> None:
        """Test worker calculation ensures minimum of 1 worker."""
        with patch("os.cpu_count", return_value=1):
            with patch.object(
                self.manager, "get_available_memory_gb", return_value=1.0
            ):
                result = self.manager.calculate_optimal_workers()
                # Should never go below 1 worker
                self.assertEqual(result, 1)

    def test_calculate_optimal_workers_error_fallback(self) -> None:
        """Test worker calculation fallback when calculation fails."""
        with patch("os.cpu_count", side_effect=Exception("Test error")):
            result = self.manager.calculate_optimal_workers()
            self.assertEqual(result, 4)  # Fallback value


if __name__ == "__main__":
    unittest.main()
