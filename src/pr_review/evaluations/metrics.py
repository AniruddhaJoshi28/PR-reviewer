"""Evaluation metrics computation for review accuracy and performance."""

from __future__ import annotations

from typing import Any

from pr_review.models.base import EvaluationMetrics, RiskLevel


def calculate_evaluation_metrics(
    runs: list[dict[str, Any]],
    benchmark_name: str = "synthetic-11-fixtures",
) -> EvaluationMetrics:
    """Calculate precision, recall, F1, and security metrics from actual benchmark runs."""
    total_fixtures = len(runs)
    if total_fixtures == 0:
        return EvaluationMetrics(benchmark_name=benchmark_name)

    true_positives = 0
    false_positives = 0
    false_negatives = 0
    true_negatives = 0

    high_risk_fn = 0
    severity_weighted_recall_sum = 0.0
    total_severity_weight = 0.0
    hallucinated = 0
    evidence_valid_count = 0
    total_findings_evaluated = 0

    total_tokens = 0
    total_latency = 0.0

    severity_weights = {
        "HIGH": 3.0,
        "MEDIUM": 2.0,
        "LOW": 1.0,
    }

    for item in runs:
        expected_risk = item.get("expected_risk", "LOW")
        actual_risk = item.get("actual_risk", "LOW")
        expected_findings = item.get("expected_findings", [])
        actual_findings = item.get("actual_findings", [])
        weight = severity_weights.get(expected_risk, 1.0)
        total_severity_weight += weight

        total_tokens += item.get("token_usage", 0)
        total_latency += item.get("latency_seconds", 0.0)

        # Risk level correctness
        if expected_risk in ("HIGH", "MEDIUM"):
            if actual_risk == expected_risk or (actual_risk == "HIGH" and expected_risk == "MEDIUM"):
                true_positives += 1
                severity_weighted_recall_sum += weight
            else:
                false_negatives += 1
                if expected_risk == "HIGH":
                    high_risk_fn += 1
        else:  # expected is LOW
            if actual_risk == "LOW":
                true_negatives += 1
                severity_weighted_recall_sum += weight
            else:
                false_positives += 1

        # Evidence validation
        for f in actual_findings:
            total_findings_evaluated += 1
            if f.get("is_hallucinated"):
                hallucinated += 1
            else:
                evidence_valid_count += 1

    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 1.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 1.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    fpr = false_positives / (false_positives + true_negatives) if (false_positives + true_negatives) > 0 else 0.0
    weighted_recall = severity_weighted_recall_sum / total_severity_weight if total_severity_weight > 0 else 1.0
    evidence_rate = evidence_valid_count / total_findings_evaluated if total_findings_evaluated > 0 else 1.0
    mean_latency = total_latency / total_fixtures if total_fixtures > 0 else 0.0

    return EvaluationMetrics(
        benchmark_name=benchmark_name,
        total_fixtures=total_fixtures,
        precision=round(precision, 4),
        recall=round(recall, 4),
        f1=round(f1, 4),
        severity_weighted_recall=round(weighted_recall, 4),
        false_positive_rate=round(fpr, 4),
        high_risk_false_negatives=high_risk_fn,
        hallucinated_findings=hallucinated,
        evidence_validity_rate=round(evidence_rate, 4),
        mean_latency_seconds=round(mean_latency, 4),
        total_tokens=total_tokens,
        estimated_cost_usd=round(total_tokens * 0.000002, 6),
    )
