"""Evidence Validation Engine.

Cross-checks agent findings against actual diff content to eliminate
hallucinated files, lines, and non-existent code snippets.
"""

from __future__ import annotations

import logging
from typing import Sequence

from pr_review.models.base import DiffFile, ReviewFinding

logger = logging.getLogger(__name__)


class EvidenceValidator:
    """Validates review findings against ground-truth diff content."""

    @staticmethod
    def validate_findings(
        findings: Sequence[ReviewFinding],
        diff_files: Sequence[DiffFile],
    ) -> tuple[list[ReviewFinding], list[dict[str, str]]]:
        """Cross-check findings against diff files.

        Returns:
            (validated_findings, rejected_findings_with_reasons)
        """
        diff_paths = {df.path: df for df in diff_files}
        # Also map basenames for flexible matching
        diff_basenames = {df.path.split("/")[-1]: df for df in diff_files}

        validated: list[ReviewFinding] = []
        rejected: list[dict[str, str]] = []

        for finding in findings:
            # 1. Path existence check
            matched_diff = diff_paths.get(finding.file_path)
            if not matched_diff:
                matched_diff = diff_basenames.get(finding.file_path.split("/")[-1])

            if not matched_diff:
                rejected.append({
                    "finding_id": finding.finding_id,
                    "reason": f"Hallucinated path: '{finding.file_path}' does not exist in PR diff.",
                })
                logger.warning(f"Rejecting finding {finding.finding_id}: path '{finding.file_path}' not in diff.")
                continue

            # 2. Evidence verification (if snippet provided)
            patch = matched_diff.patch or ""
            if finding.evidence and patch:
                # Normalize spaces for verification
                norm_evidence = " ".join(finding.evidence.strip().split())
                norm_patch = " ".join(patch.strip().split())
                if norm_evidence not in norm_patch and finding.evidence.strip() not in patch:
                    # Downgrade confidence or reject if completely fabricated
                    logger.info(
                        f"Evidence mismatch for {finding.finding_id}. "
                        "Snippet not verbatim in patch. Adjusting confidence."
                    )
                    # Create adjusted finding with reduced confidence
                    adjusted = ReviewFinding(
                        finding_id=finding.finding_id,
                        severity=finding.severity,
                        category=finding.category,
                        file_path=matched_diff.path,
                        line_start=finding.line_start,
                        line_end=finding.line_end,
                        title=finding.title,
                        description=f"{finding.description} (Note: evidence snippet not found verbatim in diff)",
                        evidence=finding.evidence,
                        suggestion=finding.suggestion,
                        confidence=max(0.2, finding.confidence * 0.7),
                        reviewer_id=finding.reviewer_id,
                    )
                    validated.append(adjusted)
                    continue

            # Fully valid
            validated.append(finding)

        return validated, rejected
