"""Unit tests for the policy engine, mandatory checks, and fail-closed rules."""

import pytest
from pr_review.models.base import (
    PolicyDecision,
    PRMetadata,
    ReviewFinding,
    RiskClassification,
    RiskLevel,
    ScanResult,
    ScanStatus,
    SCMProviderType,
)
from pr_review.policy.engine import PolicyEngine


def test_mandatory_scanner_not_run_blocks_production():
    engine = PolicyEngine()
    meta = PRMetadata(
        pr_id="1", title="Test", source_branch="a", target_branch="b",
        base_sha="1111111111111111111111111111111111111111",
        head_sha="2222222222222222222222222222222222222222",
        author="alice", provider=SCMProviderType.GENERIC_GIT
    )
    risk = RiskClassification(risk_level=RiskLevel.LOW)
    # Mandatory semgrep scanner was NOT_RUN
    scans = [
        ScanResult(scanner_name="semgrep", status=ScanStatus.NOT_RUN, passed=False, error_message="Not installed")
    ]
    res = engine.evaluate(meta, risk, scans, [], allow_mock=False)
    # In production, NOT_RUN mandatory check must fail closed (BLOCKED)
    assert res.decision == PolicyDecision.BLOCKED
    assert res.mandatory_checks_passed is False
    assert any("NOT_RUN" in r for r in res.reasons)


def test_high_risk_requires_human_approval():
    engine = PolicyEngine()
    meta = PRMetadata(
        pr_id="1", title="Test", source_branch="a", target_branch="b",
        base_sha="1111111111111111111111111111111111111111",
        head_sha="2222222222222222222222222222222222222222",
        author="alice", provider=SCMProviderType.GENERIC_GIT
    )
    risk = RiskClassification(risk_level=RiskLevel.HIGH)
    scans = [
        ScanResult(scanner_name="semgrep", status=ScanStatus.PASS, passed=True),
        ScanResult(scanner_name="gitleaks", status=ScanStatus.PASS, passed=True),
    ]
    res = engine.evaluate(meta, risk, scans, [], allow_mock=False)
    assert res.decision == PolicyDecision.HUMAN_APPROVAL_REQUIRED
    assert "security-team" in res.human_approvers


def test_stale_commit_sha_returns_incomplete():
    engine = PolicyEngine()
    meta = PRMetadata(
        pr_id="1", title="Test", source_branch="a", target_branch="b",
        base_sha="0000000000000000000000000000000000000000",
        head_sha="0000000000000000000000000000000000000000",
        author="alice", provider=SCMProviderType.GENERIC_GIT
    )
    risk = RiskClassification(risk_level=RiskLevel.LOW)
    res = engine.evaluate(meta, risk, [], [])
    assert res.decision == PolicyDecision.INCOMPLETE
