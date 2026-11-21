"""Policy Decision and Enforcement Engine."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Sequence

from pr_review.models.base import (
    PolicyDecision,
    PolicyResult,
    PRMetadata,
    ReviewFinding,
    RiskClassification,
    RiskLevel,
    ScanResult,
    ScanStatus,
)
from pr_review.policy.loader import load_policy_config

logger = logging.getLogger(__name__)


class PolicyEngine:
    """Evaluates pipeline outputs against deterministic organizational policies."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or load_policy_config()
        self.version = self.config.get("version", "1.0.0")

    def evaluate(
        self,
        pr_metadata: PRMetadata,
        risk_classification: RiskClassification,
        scan_results: Sequence[ScanResult],
        agent_findings: Sequence[ReviewFinding],
        allow_mock: bool = False,
        override: dict[str, Any] | None = None,
    ) -> PolicyResult:
        """Evaluate all findings, scanner statuses, and risk levels to determine policy decision."""
        reasons: list[str] = []
        mandatory_passed = True
        decision = PolicyDecision.PASS

        # -------------------------------------------------------------------
        # 1. Commit SHA Integrity Check
        # -------------------------------------------------------------------
        if not pr_metadata.head_sha or pr_metadata.head_sha == "0000000000000000000000000000000000000000":
            decision = PolicyDecision.INCOMPLETE
            reasons.append("Invalid or unverified commit HEAD SHA.")
            return PolicyResult(
                decision=decision,
                risk_level=risk_classification.risk_level,
                mandatory_checks_passed=False,
                reasons=reasons,
                policy_version=self.version,
                timestamp=datetime.now(timezone.utc),
            )

        # -------------------------------------------------------------------
        # 2. Mandatory Scanner Verification
        # -------------------------------------------------------------------
        mandatory_scanners = {
            m.get("scanner") for m in self.config.get("mandatory_checks", []) if m.get("must_pass")
        }

        for scan in scan_results:
            is_mandatory = scan.scanner_name in mandatory_scanners

            # Rule: NOT_RUN in production is a mandatory failure
            if scan.status == ScanStatus.NOT_RUN and is_mandatory:
                mandatory_passed = False
                reasons.append(f"Mandatory scanner '{scan.scanner_name}' was NOT_RUN: {scan.error_message}")
            elif scan.status == ScanStatus.ERROR and is_mandatory:
                mandatory_passed = False
                reasons.append(f"Mandatory scanner '{scan.scanner_name}' failed with system ERROR: {scan.error_message}")
            elif scan.status in (ScanStatus.FAIL, ScanStatus.MOCK_FAIL) and is_mandatory:
                mandatory_passed = False
                reasons.append(f"Mandatory scanner '{scan.scanner_name}' failed with {len(scan.findings)} findings.")
            elif scan.status == ScanStatus.MOCK_PASS and not allow_mock and is_mandatory:
                mandatory_passed = False
                reasons.append(f"Scanner '{scan.scanner_name}' ran in MOCK mode which is disallowed in production.")

        # -------------------------------------------------------------------
        # 3. High Severity Agent & Security Findings
        # -------------------------------------------------------------------
        high_severity_findings = [f for f in agent_findings if f.severity == RiskLevel.HIGH]
        if high_severity_findings:
            reasons.append(f"Found {len(high_severity_findings)} HIGH severity review findings.")

        # -------------------------------------------------------------------
        # 4. Determine Policy Decision (Fail-Closed)
        # -------------------------------------------------------------------
        if not mandatory_passed:
            decision = PolicyDecision.BLOCKED
        elif high_severity_findings:
            decision = PolicyDecision.BLOCKED
        elif risk_classification.risk_level == RiskLevel.HIGH:
            decision = PolicyDecision.HUMAN_APPROVAL_REQUIRED
            reasons.append("HIGH risk changeset requires mandatory two-person + security team approval.")
        elif risk_classification.risk_level == RiskLevel.MEDIUM:
            decision = PolicyDecision.HUMAN_APPROVAL_REQUIRED
            reasons.append("MEDIUM risk changeset requires human tech-lead approval.")
        else:
            decision = PolicyDecision.PASS
            reasons.append("All automated checks passed; low-risk classification.")

        # -------------------------------------------------------------------
        # 5. Handle Authorized Overrides
        # -------------------------------------------------------------------
        override_info: dict[str, Any] = {}
        if override and decision in (PolicyDecision.BLOCKED, PolicyDecision.HUMAN_APPROVAL_REQUIRED):
            allowed_roles = self.config.get("override_policy", {}).get("allowed_roles", [])
            role = override.get("role")
            reason_text = override.get("reason")
            author = override.get("author")

            if role in allowed_roles and reason_text:
                logger.info(f"Policy override accepted by {author} ({role}): {reason_text}")
                override_info = {
                    "overridden_by": author,
                    "role": role,
                    "reason": reason_text,
                    "previous_decision": decision.value,
                    "overridden_at": datetime.now(timezone.utc).isoformat(),
                }
                decision = PolicyDecision.PASS
                reasons.append(f"OVERRIDDEN by {author} ({role}): {reason_text}")
            else:
                reasons.append(f"Invalid override attempt by {author} with role '{role}'.")

        # Approver list requirements
        human_approvers: list[str] = []
        if decision == PolicyDecision.HUMAN_APPROVAL_REQUIRED:
            if risk_classification.risk_level == RiskLevel.HIGH:
                human_approvers = ["security-team", "tech-lead", "peer-reviewer"]
            else:
                human_approvers = ["peer-reviewer"]

        return PolicyResult(
            decision=decision,
            risk_level=risk_classification.risk_level,
            mandatory_checks_passed=mandatory_passed,
            reasons=reasons,
            human_approvers=human_approvers,
            override_info=override_info,
            policy_version=self.version,
            timestamp=datetime.now(timezone.utc),
        )
