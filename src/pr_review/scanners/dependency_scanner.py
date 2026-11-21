"""Dependency vulnerability scanner (pip-audit)."""

from __future__ import annotations

import json
import logging
import subprocess
from typing import Any

from pr_review.models.base import DiffFile, ScanResult, ScanStatus
from pr_review.scanners.base import SecurityScanner

logger = logging.getLogger(__name__)


class DependencyScanner(SecurityScanner):
    """Integrates pip-audit for dependency vulnerability scanning."""

    def __init__(self, is_mandatory: bool = True, offline_mock: bool = False) -> None:
        super().__init__(name="pip-audit", is_mandatory=is_mandatory, offline_mock=offline_mock)

    def binary_name(self) -> str:
        return "pip-audit"

    def run_scan(self, diff_files: list[DiffFile], target_dir: str = ".") -> ScanResult:
        cmd = ["pip-audit", "--format", "json"]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=120)
            if res.returncode not in (0, 1):
                return ScanResult(
                    scanner_name=self.name,
                    status=ScanStatus.ERROR,
                    passed=False,
                    error_message=f"pip-audit error exit code {res.returncode}: {res.stderr[:200]}",
                )

            data = json.loads(res.stdout) if res.stdout else {}
            vulns = data.get("dependencies", [])
            found_vulns: list[dict[str, Any]] = []
            for dep in vulns:
                for v in dep.get("vulns", []):
                    found_vulns.append({
                        "package": dep.get("name"),
                        "version": dep.get("version"),
                        "vuln_id": v.get("id"),
                        "fix_versions": v.get("fix_versions"),
                        "description": v.get("description"),
                    })

            passed = len(found_vulns) == 0
            status = ScanStatus.PASS if passed else ScanStatus.FAIL
            return ScanResult(
                scanner_name=self.name,
                status=status,
                passed=passed,
                findings=found_vulns,
            )
        except Exception as e:
            return ScanResult(
                scanner_name=self.name,
                status=ScanStatus.ERROR,
                passed=False,
                error_message=f"pip-audit execution exception: {e}",
            )

    def run_mock_scan(self, diff_files: list[DiffFile], target_dir: str = ".") -> ScanResult:
        """Mock dependency scan checking for pinned vulnerable test packages."""
        findings: list[dict[str, Any]] = []
        for f in diff_files:
            if "requirements" in f.path or "pyproject.toml" in f.path:
                patch = f.patch or ""
                if "insecure-package" in patch or "vulnerable-lib==0.1.0" in patch:
                    findings.append({
                        "package": "vulnerable-lib",
                        "version": "0.1.0",
                        "vuln_id": "CVE-2026-MOCK-9999",
                        "description": "Mock vulnerable package detected in dependencies.",
                    })

        passed = len(findings) == 0
        return ScanResult(
            scanner_name=self.name,
            status=ScanStatus.MOCK_PASS if passed else ScanStatus.MOCK_FAIL,
            passed=passed,
            is_mock=True,
            findings=findings,
        )
