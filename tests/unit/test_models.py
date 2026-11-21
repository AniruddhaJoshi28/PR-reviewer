"""Unit tests for Pydantic v2 data models and serialization."""

import pytest
from pydantic import ValidationError
from pr_review.models.base import DiffFile, PRMetadata, RiskLevel, SCMProviderType, ScanResult, ScanStatus


def test_diff_file_frozen_immutability():
    diff = DiffFile(path="test.py", status="M")
    with pytest.raises(ValidationError):
        # Immutable models cannot be modified in place
        diff.path = "modified.py"


def test_scan_result_serialization():
    scan = ScanResult(
        scanner_name="semgrep",
        status=ScanStatus.PASS,
        passed=True,
        findings=[{"rule": "sqli", "file": "db.py"}],
    )
    dumped = scan.model_dump()
    assert dumped["status"] == "PASS"
    assert dumped["passed"] is True
    assert len(dumped["findings"]) == 1
