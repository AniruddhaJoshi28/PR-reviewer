"""SARIF 2.1.0 report generator for static analysis and review findings."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pr_review.models.base import ReviewReport, RiskLevel


class SARIFReporter:
    """Generates standard SARIF 2.1.0 output for Jenkins Warnings NG and GitHub/GitLab ingestion."""

    @staticmethod
    def generate_sarif(report: ReviewReport, output_path: str | Path) -> str:
        results: list[dict[str, Any]] = []

        # Convert agent findings into SARIF results
        for rev in report.agent_reviews:
            for f in rev.findings:
                level_map = {
                    RiskLevel.HIGH: "error",
                    RiskLevel.MEDIUM: "warning",
                    RiskLevel.LOW: "note",
                }
                sarif_level = level_map.get(f.severity, "warning")

                start_line = f.line_start or 1
                end_line = f.line_end or start_line

                results.append({
                    "ruleId": f.finding_id,
                    "level": sarif_level,
                    "message": {"text": f"{f.title}: {f.description}"},
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {"uri": f.file_path},
                                "region": {
                                    "startLine": start_line,
                                    "endLine": end_line,
                                },
                            }
                        }
                    ],
                })

        # Add scanner findings
        for s in report.scan_results:
            for sf in s.findings:
                results.append({
                    "ruleId": sf.get("check_id") or sf.get("rule_id") or s.scanner_name,
                    "level": "error" if s.status.value in ("FAIL", "MOCK_FAIL") else "warning",
                    "message": {"text": sf.get("message") or sf.get("description") or f"Finding from {s.scanner_name}"},
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {"uri": sf.get("path") or sf.get("file") or "unknown"},
                                "region": {"startLine": sf.get("start_line") or 1},
                            }
                        }
                    ],
                })

        sarif_doc = {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "jenkins-agentic-pr-review",
                            "semanticVersion": report.pipeline_version or "1.0.0",
                            "informationUri": "https://github.com/AniruddhaJoshi28/PR-reviewer",
                        }
                    },
                    "results": results,
                }
            ],
        }

        content = json.dumps(sarif_doc, indent=2)
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(content, encoding="utf-8")
        return content
