"""Unit tests for deterministic risk classification and rule enforcement."""

import pytest
from pr_review.models.base import DiffFile, PRMetadata, RiskLevel, SCMProviderType
from pr_review.risk.classifier import RiskClassifier


def test_classify_high_risk_auth_path():
    classifier = RiskClassifier()
    diffs = [DiffFile(path="src/auth/login.py", status="M")]
    res = classifier.classify(diffs)
    assert res.risk_level == RiskLevel.HIGH
    assert "RULE_HIGH_AUTH_PATH" in res.rule_ids


def test_classify_high_risk_sql_injection():
    classifier = RiskClassifier()
    diffs = [
        DiffFile(
            path="src/repo.py",
            status="M",
            patch="+query = f\"SELECT * FROM users WHERE id = '{user_id}'\"\n",
        )
    ]
    res = classifier.classify(diffs)
    assert res.risk_level == RiskLevel.HIGH
    assert "RULE_HIGH_SQL_EXECUTION" in res.rule_ids


def test_classify_low_risk_documentation():
    classifier = RiskClassifier()
    diffs = [DiffFile(path="docs/architecture.md", status="M", patch="+# New Heading\n")]
    res = classifier.classify(diffs)
    assert res.risk_level == RiskLevel.LOW
    assert "RULE_LOW_DOCUMENTATION" in res.rule_ids


def test_classify_unknown_file_defaults_to_medium():
    classifier = RiskClassifier()
    diffs = [DiffFile(path="custom_widget.foo", status="M", patch="+var x = 1;\n")]
    res = classifier.classify(diffs)
    # MUST NOT default to LOW!
    assert res.risk_level == RiskLevel.MEDIUM
    assert "RULE_UNKNOWN_FILE_DEFAULT_MED" in res.rule_ids


def test_ai_cannot_downgrade_deterministic_high():
    classifier = RiskClassifier()
    diffs = [DiffFile(path="src/auth/token.py", status="M")]
    det = classifier.classify(diffs)
    assert det.risk_level == RiskLevel.HIGH

    # AI attempts to claim it's LOW
    escalated = RiskClassifier.apply_ai_escalation(det, RiskLevel.LOW, "AI says it is safe")
    assert escalated.risk_level == RiskLevel.HIGH  # Downgrade rejected!


def test_ai_can_escalate_medium_to_high():
    classifier = RiskClassifier()
    diffs = [DiffFile(path="src/business_logic.py", status="M", patch="+def calculate_tier(): pass\n")]
    det = classifier.classify(diffs)
    assert det.risk_level == RiskLevel.MEDIUM

    escalated = RiskClassifier.apply_ai_escalation(det, RiskLevel.HIGH, "Complex hidden state found")
    assert escalated.risk_level == RiskLevel.HIGH
    assert "RULE_AI_ESCALATED" in escalated.rule_ids
