"""Semgrep static analysis scanner."""

from __future__ import annotations

import json
import logging
import re
import subprocess
from typing import Any

from pr_review.models.base import DiffFile, ScanResult, ScanStatus
from pr_review.scanners.base import SecurityScanner

logger = logging.getLogger(__name__)


class SemgrepScanner(SecurityScanner):
    """Integrates Semgrep SAST scanner."""

    def __init__(self, is_mandatory: bool = True, offline_mock: bool = False) -> None:
        super().__init__(name="semgrep", is_mandatory=is_mandatory, offline_mock=offline_mock)

    def binary_name(self) -> str:
        return "semgrep"

    def run_scan(self, diff_files: list[DiffFile], target_dir: str = ".") -> ScanResult:
        cmd = ["semgrep", "scan", "--json", "--quiet", target_dir]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=120)
            if res.returncode not in (0, 1):  # Semgrep returns 1 when findings found or 0 on clean
                return ScanResult(
                    scanner_name=self.name,
                    status=ScanStatus.ERROR,
                    passed=False,
                    error_message=f"Semgrep exited with code {res.returncode}: {res.stderr[:200]}",
                )

            data = json.loads(res.stdout) if res.stdout else {}
            results = data.get("results", [])
            passed = len(results) == 0
            status = ScanStatus.PASS if passed else ScanStatus.FAIL

            findings = [
                {
                    "check_id": r.get("check_id"),
                    "path": r.get("path"),
                    "start": r.get("start", {}),
                    "message": r.get("extra", {}).get("message"),
                    "severity": r.get("extra", {}).get("severity"),
                }
                for r in results
            ]
            return ScanResult(
                scanner_name=self.name,
                status=status,
                passed=passed,
                findings=findings,
            )
        except Exception as e:
            return ScanResult(
                scanner_name=self.name,
                status=ScanStatus.ERROR,
                passed=False,
                error_message=f"Failed to execute semgrep: {e}",
            )

    def run_mock_scan(self, diff_files: list[DiffFile], target_dir: str = ".") -> ScanResult:
        """Mock Semgrep scanner using regex rules for SQL injection and unsafe functions."""
        findings: list[dict[str, Any]] = []

        sql_inj_pattern = re.compile(r"(?i)(SELECT|INSERT|UPDATE|DELETE).*(f['\"]|\.format\(|%\s*\()")
        exec_pattern = re.compile(r"(?i)\b(eval|exec)\s*\(")

        for f in diff_files:
            patch = f.patch or ""
            if sql_inj_pattern.search(patch):
                findings.append({
                    "check_id": "python.lang.security.audit.sqli",
                    "path": f.path,
                    "message": "Potential SQL injection via formatted query string.",
                    "severity": "ERROR",
                })
            if exec_pattern.search(patch):
                findings.append({
                    "check_id": "python.lang.security.audit.exec",
                    "path": f.path,
                    "message": "Use of unsafe dynamic execution primitive (eval/exec).",
                    "severity": "WARNING",
                })

        passed = len(findings) == 0
        return ScanResult(
            scanner_name=self.name,
            status=ScanStatus.MOCK_PASS if passed else ScanStatus.MOCK_FAIL,
            passed=passed,
            is_mock=True,
            findings=findings,
        )
