"""Report Orchestrator coordinating all artifact writers."""

from __future__ import annotations

import logging
from pathlib import Path

from pr_review.models.base import ReviewReport
from pr_review.reporting.json_reporter import JSONReporter
from pr_review.reporting.junit_reporter import JUnitReporter
from pr_review.reporting.markdown_reporter import MarkdownReporter
from pr_review.reporting.sarif_reporter import SARIFReporter

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Orchestrates generation of all required Jenkins review artifacts."""

    def __init__(self, artifacts_dir: str | Path = "artifacts") -> None:
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def generate_all(self, report: ReviewReport) -> dict[str, str]:
        """Generate review.json, review.md, review.sarif, tests.xml, and policy-decision.json.

        Returns dictionary of paths to generated artifacts.
        """
        paths = {
            "review_json": str(self.artifacts_dir / "review.json"),
            "review_md": str(self.artifacts_dir / "review.md"),
            "review_sarif": str(self.artifacts_dir / "review.sarif"),
            "tests_xml": str(self.artifacts_dir / "tests.xml"),
            "policy_json": str(self.artifacts_dir / "policy-decision.json"),
        }

        logger.info(f"Generating review artifacts into: {self.artifacts_dir}")
        JSONReporter.generate_review_json(report, paths["review_json"])
        MarkdownReporter.generate_review_md(report, paths["review_md"])
        SARIFReporter.generate_sarif(report, paths["review_sarif"])
        JUnitReporter.generate_junit(report, paths["tests_xml"])
        JSONReporter.generate_policy_json(report, paths["policy_json"])

        logger.info("All 5 review artifacts generated successfully.")
        return paths
