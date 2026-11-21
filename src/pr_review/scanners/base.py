"""Base interface for security and quality scanners."""

from __future__ import annotations

from abc import ABC, abstractmethod
import shutil
import time
from typing import Any

from pr_review.models.base import DiffFile, ScanResult, ScanStatus


class SecurityScanner(ABC):
    """Abstract base class for security scanners."""

    def __init__(self, name: str, is_mandatory: bool = True, offline_mock: bool = False) -> None:
        self.name = name
        self.is_mandatory = is_mandatory
        self.offline_mock = offline_mock

    @abstractmethod
    def binary_name(self) -> str:
        """Name of the required CLI executable."""
        ...

    def is_installed(self) -> bool:
        """Check if scanner binary is available on PATH."""
        return shutil.which(self.binary_name()) is not None

    @abstractmethod
    def run_scan(self, diff_files: list[DiffFile], target_dir: str = ".") -> ScanResult:
        """Perform the actual scan using the installed CLI tool."""
        ...

    @abstractmethod
    def run_mock_scan(self, diff_files: list[DiffFile], target_dir: str = ".") -> ScanResult:
        """Perform a deterministic mock scan for offline demonstrations and test fixtures."""
        ...

    def scan(self, diff_files: list[DiffFile], target_dir: str = ".") -> ScanResult:
        """Execute scanner. If tool is missing, returns NOT_RUN (or MOCK in offline mode)."""
        start = time.perf_counter()

        if self.offline_mock:
            result = self.run_mock_scan(diff_files, target_dir)
            elapsed = time.perf_counter() - start
            return ScanResult(
                scanner_name=self.name,
                status=result.status,
                passed=result.passed,
                is_mock=True,
                findings=result.findings,
                sarif_path=result.sarif_path,
                error_message=result.error_message,
                execution_time_seconds=round(elapsed, 4),
            )

        if not self.is_installed():
            elapsed = time.perf_counter() - start
            return ScanResult(
                scanner_name=self.name,
                status=ScanStatus.NOT_RUN,
                passed=False,
                is_mock=False,
                findings=[],
                error_message=f"Scanner binary '{self.binary_name()}' is not installed or not found on PATH.",
                execution_time_seconds=round(elapsed, 4),
            )

        try:
            result = self.run_scan(diff_files, target_dir)
            elapsed = time.perf_counter() - start
            return ScanResult(
                scanner_name=self.name,
                status=result.status,
                passed=result.passed,
                is_mock=False,
                findings=result.findings,
                sarif_path=result.sarif_path,
                error_message=result.error_message,
                execution_time_seconds=round(elapsed, 4),
            )
        except Exception as e:
            elapsed = time.perf_counter() - start
            return ScanResult(
                scanner_name=self.name,
                status=ScanStatus.ERROR,
                passed=False,
                is_mock=False,
                findings=[],
                error_message=f"Scanner execution exception: {str(e)}",
                execution_time_seconds=round(elapsed, 4),
            )
