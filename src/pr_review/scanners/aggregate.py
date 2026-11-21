"""Scanner orchestrator coordinating all security and quality scanners."""

from __future__ import annotations

import logging
from typing import Sequence

from pr_review.models.base import DiffFile, ScanResult, ScanStatus
from pr_review.scanners.base import SecurityScanner
from pr_review.scanners.dependency_scanner import DependencyScanner
from pr_review.scanners.gitleaks_scanner import GitleaksScanner
from pr_review.scanners.semgrep_scanner import SemgrepScanner

logger = logging.getLogger(__name__)


class ScannerOrchestrator:
    """Orchestrates security scanning with strict error and availability handling."""

    def __init__(
        self,
        scanners: Sequence[SecurityScanner] | None = None,
        offline_demo: bool = False,
    ) -> None:
        self.offline_demo = offline_demo
        if scanners is not None:
            self.scanners = list(scanners)
        else:
            self.scanners = [
                SemgrepScanner(is_mandatory=True, offline_mock=offline_demo),
                GitleaksScanner(is_mandatory=True, offline_mock=offline_demo),
                DependencyScanner(is_mandatory=False, offline_mock=offline_demo),
            ]

    def scan_all(self, diff_files: list[DiffFile], target_dir: str = ".") -> list[ScanResult]:
        """Run all scanners and collect results."""
        results: list[ScanResult] = []
        for scanner in self.scanners:
            logger.info(f"Executing scanner: {scanner.name} (mandatory={scanner.is_mandatory}, mock={self.offline_demo})")
            result = scanner.scan(diff_files, target_dir)
            logger.info(
                f"Scanner {scanner.name} finished with status={result.status.value}, "
                f"passed={result.passed}, findings={len(result.findings)}"
            )
            results.append(result)
        return results

    @staticmethod
    def are_mandatory_scanners_satisfied(results: list[ScanResult], allow_mock: bool = False) -> tuple[bool, list[str]]:
        """Verify whether all mandatory scanners passed.

        In production (allow_mock=False):
        - Any NOT_RUN, FAIL, or ERROR blocks approval.
        In offline demo (allow_mock=True):
        - MOCK_PASS is accepted, but MOCK_FAIL or NOT_RUN still blocks.
        """
        issues: list[str] = []
        for r in results:
            if r.status == ScanStatus.NOT_RUN:
                issues.append(f"Mandatory scanner '{r.scanner_name}' was NOT_RUN: {r.error_message}")
            elif r.status == ScanStatus.ERROR:
                issues.append(f"Mandatory scanner '{r.scanner_name}' encountered ERROR: {r.error_message}")
            elif r.status == ScanStatus.FAIL:
                issues.append(f"Mandatory scanner '{r.scanner_name}' FAILED with {len(r.findings)} findings.")
            elif r.status == ScanStatus.MOCK_FAIL:
                issues.append(f"Mandatory scanner '{r.scanner_name}' (MOCK) FAILED with {len(r.findings)} findings.")
            elif r.status == ScanStatus.MOCK_PASS and not allow_mock:
                issues.append(f"Scanner '{r.scanner_name}' produced MOCK_PASS which is not permitted in production.")

        all_satisfied = len(issues) == 0
        return all_satisfied, issues
