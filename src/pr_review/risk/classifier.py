"""Deterministic Risk Classification Engine."""

from __future__ import annotations

import logging
from typing import Sequence

from pr_review.models.base import DiffFile, PRMetadata, RiskClassification, RiskLevel
from pr_review.risk.rules import DEFAULT_RULES, RiskRule

logger = logging.getLogger(__name__)


class RiskClassifier:
    """Classifies PR risk deterministically based on paths, diff content, and policy rules."""

    def __init__(self, rules: Sequence[RiskRule] | None = None, policy_version: str = "1.0.0") -> None:
        self.rules = list(rules) if rules is not None else DEFAULT_RULES
        self.policy_version = policy_version

    def classify(self, diff_files: list[DiffFile], pr_metadata: PRMetadata | None = None) -> RiskClassification:
        """Classify pull request risk.

        Unknown files never default to LOW.
        If diff_files is empty or no files match, defaults to MEDIUM.
        """
        if not diff_files:
            return RiskClassification(
                risk_level=RiskLevel.MEDIUM,
                rule_ids=["RULE_DEFAULT_UNKNOWN"],
                evidence=["No diff files found or empty changeset; defaulting to MEDIUM risk."],
                affected_files=[],
                reasoning_summary="Empty or unparsed changeset defaulted to MEDIUM risk for safety.",
                policy_version=self.policy_version,
            )

        matched_high_rules: list[str] = []
        matched_med_rules: list[str] = []
        matched_low_rules: list[str] = []
        evidence_list: list[str] = []
        affected_files_set: set[str] = set()

        # Check PR description for prompt injection
        if pr_metadata and pr_metadata.description:
            for rule in self.rules:
                if rule.risk_level == RiskLevel.HIGH:
                    for pattern in rule.content_patterns:
                        if pattern.search(pr_metadata.description):
                            matched_high_rules.append(rule.rule_id)
                            evidence_list.append(f"PR description matched {rule.rule_id}: {pattern.pattern}")

        for diff_file in diff_files:
            path = diff_file.path
            patch_content = diff_file.patch or ""
            file_has_match = False

            # Evaluate each rule
            for rule in self.rules:
                # Path match
                path_matched = False
                for pattern in rule.path_patterns:
                    if pattern.search(path):
                        path_matched = True
                        file_has_match = True
                        affected_files_set.add(path)
                        evidence_str = f"File '{path}' matched path rule {rule.rule_id}"
                        if rule.risk_level == RiskLevel.HIGH:
                            matched_high_rules.append(rule.rule_id)
                            evidence_list.append(evidence_str)
                        elif rule.risk_level == RiskLevel.MEDIUM:
                            matched_med_rules.append(rule.rule_id)
                            evidence_list.append(evidence_str)
                        else:
                            matched_low_rules.append(rule.rule_id)
                        break

                # Content match (in patch)
                if patch_content:
                    for pattern in rule.content_patterns:
                        m = pattern.search(patch_content)
                        if m:
                            file_has_match = True
                            affected_files_set.add(path)
                            snippet = m.group(0)[:60]
                            evidence_str = f"File '{path}' matched content rule {rule.rule_id} on: '{snippet}'"
                            if rule.risk_level == RiskLevel.HIGH:
                                matched_high_rules.append(rule.rule_id)
                                evidence_list.append(evidence_str)
                            elif rule.risk_level == RiskLevel.MEDIUM:
                                matched_med_rules.append(rule.rule_id)
                                evidence_list.append(evidence_str)
                            else:
                                matched_low_rules.append(rule.rule_id)
                            break

            # Unknown changes must NOT default to LOW
            if not file_has_match:
                matched_med_rules.append("RULE_UNKNOWN_FILE_DEFAULT_MED")
                evidence_list.append(f"File '{path}' did not match any known rule; safe default is MEDIUM.")
                affected_files_set.add(path)

        # Determine overall deterministic risk
        if matched_high_rules:
            overall_risk = RiskLevel.HIGH
            unique_rules = list(dict.fromkeys(matched_high_rules + matched_med_rules))
            reasoning = f"High-risk rules triggered: {', '.join(set(matched_high_rules))}."
        elif matched_med_rules:
            overall_risk = RiskLevel.MEDIUM
            unique_rules = list(dict.fromkeys(matched_med_rules))
            reasoning = f"Medium-risk rules triggered: {', '.join(set(matched_med_rules))}."
        else:
            overall_risk = RiskLevel.LOW
            unique_rules = list(dict.fromkeys(matched_low_rules))
            reasoning = "All modified files matched low-risk criteria (documentation/tests) with no higher-risk signals."

        return RiskClassification(
            risk_level=overall_risk,
            rule_ids=unique_rules,
            evidence=evidence_list,
            affected_files=sorted(affected_files_set),
            reasoning_summary=reasoning,
            policy_version=self.policy_version,
        )

    @staticmethod
    def apply_ai_escalation(
        deterministic_classification: RiskClassification,
        ai_assessed_level: RiskLevel | None,
        escalation_reason: str = "",
    ) -> RiskClassification:
        """AI may escalate risk, but cannot downgrade a deterministic classification."""
        if not ai_assessed_level:
            return deterministic_classification

        current_level = deterministic_classification.risk_level
        hierarchy = {RiskLevel.LOW: 1, RiskLevel.MEDIUM: 2, RiskLevel.HIGH: 3}

        if hierarchy[ai_assessed_level] > hierarchy[current_level]:
            new_evidence = list(deterministic_classification.evidence)
            new_evidence.append(f"AI escalated risk from {current_level.value} to {ai_assessed_level.value}: {escalation_reason}")
            new_rules = list(deterministic_classification.rule_ids) + ["RULE_AI_ESCALATED"]
            return RiskClassification(
                risk_level=ai_assessed_level,
                rule_ids=new_rules,
                evidence=new_evidence,
                affected_files=deterministic_classification.affected_files,
                reasoning_summary=f"Risk escalated by AI review ({escalation_reason}). Original: {current_level.value}",
                policy_version=deterministic_classification.policy_version,
            )

        # AI cannot downgrade!
        return deterministic_classification
