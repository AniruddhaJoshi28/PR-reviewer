"""Integration test running the full evaluation benchmark across all 11 fixtures."""

from pathlib import Path
from evaluations.runner import EvaluationRunner


def test_evaluation_runner_generates_benchmark_artifacts(tmp_path: Path):
    runner = EvaluationRunner(
        fixtures_dir="evaluations/fixtures",
        labels_path="evaluations/ground_truth/labels.json",
        artifacts_dir=str(tmp_path),
    )
    summary = runner.run_benchmark()

    assert summary["fixtures_count"] == 11
    assert "Combined" in summary["metrics"]
    assert "Multi-Agent" in summary["metrics"]

    # Ensure zero high-risk false negatives in combined mode
    assert summary["metrics"]["Combined"]["high_risk_false_negatives"] == 0

    # Ensure reports exist
    assert (tmp_path / "evaluation.json").exists()
    assert (tmp_path / "evaluation.md").exists()
    assert (tmp_path / "evaluation.xml").exists()
