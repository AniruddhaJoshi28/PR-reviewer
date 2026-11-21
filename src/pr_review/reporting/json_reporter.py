"""JSON report generator for review results and policy decisions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pr_review.models.base import ReviewReport


class JSONReporter:
    """Generates machine-readable JSON reports."""

    @staticmethod
    def generate_review_json(report: ReviewReport, output_path: str | Path) -> str:
        """Serialize ReviewReport to formatted JSON and save to disk."""
        data = report.model_dump(mode="json")
        json_str = json.dumps(data, indent=2)
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json_str, encoding="utf-8")
        return json_str

    @staticmethod
    def generate_policy_json(report: ReviewReport, output_path: str | Path) -> str:
        """Save isolated policy decision artifact."""
        policy_data = report.policy_result.model_dump(mode="json") if report.policy_result else {}
        json_str = json.dumps(policy_data, indent=2)
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json_str, encoding="utf-8")
        return json_str
