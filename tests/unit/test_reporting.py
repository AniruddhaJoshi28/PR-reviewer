"""Unit tests for report generation across all 5 artifacts."""

import json
from pathlib import Path
from pr_review.models.base import (
    PolicyDecision,
    PolicyResult,
    PRMetadata,
    ReviewReport,
    RiskClassification,
    RiskLevel,
    ScanResult,
    ScanStatus,
    SCMProviderType,
)
from pr_review.reporting.generator import ReportGenerator


def test_generate_all_reports(tmp_path: Path):
    meta = PRMetadata(
        pr_id="99",
        title="Payment update",
        source_branch="feat",
        target_branch="main",
        base_sha="1111111111111111111111111111111111111111",
        head_sha="2222222222222222222222222222222222222222",
        author="bob",
        provider=SCMProviderType.GITHUB,
    )
    risk = RiskClassification(risk_level=RiskLevel.LOW)
    scans = [ScanResult(scanner_name="semgrep", status=ScanStatus.PASS, passed=True)]
    policy = PolicyResult(
        decision=PolicyDecision.PASS,
        risk_level=RiskLevel.LOW,
        mandatory_checks_passed=True,
    )
    report = ReviewReport(
        pr_metadata=meta,
        risk_classification=risk,
        scan_results=scans,
        policy_result=policy,
    )

    gen = ReportGenerator(artifacts_dir=tmp_path)
    paths = gen.generate_all(report)

    assert Path(paths["review_json"]).exists()
    assert Path(paths["review_md"]).exists()
    assert Path(paths["review_sarif"]).exists()
    assert Path(paths["tests_xml"]).exists()
    assert Path(paths["policy_json"]).exists()

    # Verify SARIF format
    sarif_data = json.loads(Path(paths["review_sarif"]).read_text())
    assert sarif_data["version"] == "2.1.0"
