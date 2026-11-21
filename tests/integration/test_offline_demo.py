"""Integration test executing the full offline pipeline demonstration."""

from pathlib import Path
from pr_review.models.base import PolicyDecision, RiskLevel
from pr_review.orchestration.pipeline import ReviewPipeline


def test_offline_demo_end_to_end(tmp_path: Path):
    pipeline = ReviewPipeline(artifacts_dir=str(tmp_path), offline_demo=True, ai_provider="offline")
    report = pipeline.run_offline_demo()

    # Verify complete pipeline execution
    assert report.pr_metadata.pr_id == "101"
    assert report.risk_classification.risk_level == RiskLevel.HIGH
    assert len(report.scan_results) == 3
    assert len(report.agent_reviews) >= 1
    assert len(report.debate_rounds) >= 1

    # Verify policy decision
    assert report.policy_result is not None
    assert report.policy_result.decision in (PolicyDecision.BLOCKED, PolicyDecision.HUMAN_APPROVAL_REQUIRED)

    # Verify all 5 artifacts were written
    assert (tmp_path / "review.json").exists()
    assert (tmp_path / "review.md").exists()
    assert (tmp_path / "review.sarif").exists()
    assert (tmp_path / "tests.xml").exists()
    assert (tmp_path / "policy-decision.json").exists()
