"""Unit tests for scanner orchestration and status reporting."""

import pytest
from pr_review.models.base import DiffFile, ScanStatus
from pr_review.scanners.aggregate import ScannerOrchestrator
from pr_review.scanners.semgrep_scanner import SemgrepScanner
from pr_review.scanners.gitleaks_scanner import GitleaksScanner


def test_missing_scanner_returns_not_run():
    # Real scanner without binary installed returns NOT_RUN, never PASS
    scanner = SemgrepScanner(offline_mock=False)
    diff = [DiffFile(path="main.py", status="M")]
    # If semgrep is not on the test runner machine, it must return NOT_RUN or ERROR
    res = scanner.scan(diff)
    if not scanner.is_installed():
        assert res.status == ScanStatus.NOT_RUN
        assert res.passed is False
        assert "not found on PATH" in res.error_message


def test_mock_scanner_flags_secrets_accurately():
    scanner = GitleaksScanner(offline_mock=True)
    diff = [
        DiffFile(
            path="src/config.py",
            status="M",
            patch="+AWS_SECRET_ACCESS_KEY = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'\n",
        )
    ]
    res = scanner.scan(diff)
    assert res.is_mock is True
    assert res.status == ScanStatus.MOCK_FAIL
    assert len(res.findings) >= 1
    assert res.findings[0]["secret"] == "***REDACTED***"  # Never leaks raw secret!
