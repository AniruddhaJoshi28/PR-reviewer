"""Gitleaks secret detection scanner."""

from __future__ import annotations

import json
import logging
import re
import subprocess
from typing import Any

from pr_review.models.base import DiffFile, ScanResult, ScanStatus
from pr_review.scanners.base import SecurityScanner

logger = logging.getLogger(__name__)


class GitleaksScanner(SecurityScanner):
    """Integrates Gitleaks secret and token scanner."""

    def __init__(self, is_mandatory: bool = True, offline_mock: bool = False) -> None:
        super().__init__(name="gitleaks", is_mandatory=is_mandatory, offline_mock=offline_mock)

    def binary_name(self) -> str:
        return "gitleaks"

    def run_scan(self, diff_files: list[DiffFile], target_dir: str = ".") -> ScanResult:
        cmd = ["gitleaks", "detect", "--no-git", "--source", target_dir, "--report-format", "json"]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=60)
            # Gitleaks exits with 1 when leaks are found, 0 when clean
            if res.returncode not in (0, 1):
                return ScanResult(
                    scanner_name=self.name,
                    status=ScanStatus.ERROR,
                    passed=False,
                    error_message=f"Gitleaks error exit code {res.returncode}: {res.stderr[:200]}",
                )

            data = json.loads(res.stdout) if res.stdout else []
            passed = len(data) == 0
            status = ScanStatus.PASS if passed else ScanStatus.FAIL
            findings = [
                {
                    "rule_id": leak.get("RuleID"),
                    "file": leak.get("File"),
                    "start_line": leak.get("StartLine"),
                    "secret": "***REDACTED***",
                    "description": leak.get("Description"),
                }
                for leak in data
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
                error_message=f"Gitleaks execution exception: {e}",
            )

    def run_mock_scan(self, diff_files: list[DiffFile], target_dir: str = ".") -> ScanResult:
        """Mock Gitleaks scanner detecting AWS keys and private keys."""
        findings: list[dict[str, Any]] = []

        patterns = [
            (re.compile(r"AKIA[0-9A-Z]{16}"), "aws-access-key-id", "AWS Access Key ID"),
            (re.compile(r"(?i)aws_secret_access_key\s*=\s*['\"][A-Za-z0-9/+=]{30,}['\"]"), "aws-secret-key", "AWS Secret Key"),
            (re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"), "private-key", "Private Key"),
        ]

        for f in diff_files:
            patch = f.patch or ""
            for pat, rule_id, desc in patterns:
                if pat.search(patch):
                    findings.append({
                        "rule_id": rule_id,
                        "file": f.path,
                        "description": desc,
                        "secret": "***REDACTED***",
                    })

        passed = len(findings) == 0
        return ScanResult(
            scanner_name=self.name,
            status=ScanStatus.MOCK_PASS if passed else ScanStatus.MOCK_FAIL,
            passed=passed,
            is_mock=True,
            findings=findings,
        )
