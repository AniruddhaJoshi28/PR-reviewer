"""Unit tests for evidence validator and hallucination detection."""

import pytest
from pr_review.evidence.validator import EvidenceValidator
from pr_review.models.base import DiffFile, ReviewFinding, RiskLevel


def test_evidence_validator_rejects_hallucinated_file():
    diffs = [DiffFile(path="src/real_file.py", status="M", patch="+x = 1\n")]
    findings = [
        ReviewFinding(
            finding_id="F-1",
            severity=RiskLevel.HIGH,
            category="security",
            file_path="src/phantom_ghost_file.py",  # Not in diff!
            title="Ghost bug",
            description="Fake finding in non-existent file",
        )
    ]
    validated, rejected = EvidenceValidator.validate_findings(findings, diffs)
    assert len(validated) == 0
    assert len(rejected) == 1
    assert "Hallucinated path" in rejected[0]["reason"]


def test_evidence_validator_accepts_valid_finding():
    diffs = [DiffFile(path="src/app.py", status="M", patch="+API_KEY = 'secret123'\n")]
    findings = [
        ReviewFinding(
            finding_id="F-2",
            severity=RiskLevel.HIGH,
            category="security",
            file_path="src/app.py",
            title="Hardcoded API key",
            description="Found API key in code",
            evidence="API_KEY = 'secret123'",
        )
    ]
    validated, rejected = EvidenceValidator.validate_findings(findings, diffs)
    assert len(validated) == 1
    assert len(rejected) == 0
