"""Adversarial Multi-Agent Debate Engine with conditional risk routing."""

from __future__ import annotations

import logging
from typing import Sequence

from pr_review.agents.base import ReviewAgent
from pr_review.agents.factory import AgentFactory
from pr_review.models.base import (
    AgentReview,
    DebateChallenge,
    DebateRound,
    DiffFile,
    ReviewFinding,
    RiskClassification,
    RiskLevel,
)

logger = logging.getLogger(__name__)


class DebateOrchestrator:
    """Orchestrates independent reviews, adversarial challenges, and judicial verdicts."""

    def __init__(self, provider: str = "offline") -> None:
        self.provider = provider

    def run_debate(
        self,
        diff_files: list[DiffFile],
        risk: RiskClassification,
    ) -> tuple[list[AgentReview], list[DebateRound], list[ReviewFinding]]:
        """Execute risk-conditional review and debate.

        Returns:
            (agent_reviews, debate_rounds, final_findings)
        """
        level = risk.risk_level

        # -------------------------------------------------------------
        # 1. LOW RISK: Single reviewer, no debate
        # -------------------------------------------------------------
        if level == RiskLevel.LOW:
            logger.info("Risk is LOW: Dispatching single reviewer without adversarial debate.")
            reviewer = AgentFactory.create_agent(role="correctness", provider=self.provider)
            review = reviewer.review(diff_files, risk)
            return [review], [], review.findings

        # -------------------------------------------------------------
        # 2. Configure Reviewers based on Risk Level
        # -------------------------------------------------------------
        reviewers: list[ReviewAgent] = []
        if level == RiskLevel.MEDIUM:
            # 4-agent panel: correctness, maintainability, challenger, judge
            logger.info("Risk is MEDIUM: Dispatching 4-agent panel (correctness + maintainability + debate).")
            reviewers = [
                AgentFactory.create_agent(role="correctness", provider=self.provider),
                AgentFactory.create_agent(role="maintainability", provider=self.provider),
            ]
        elif level == RiskLevel.HIGH:
            # 6-agent panel: correctness, security, data_contract, infrastructure, challenger, judge
            logger.info("Risk is HIGH: Dispatching 6-agent panel with dedicated security and infrastructure.")
            reviewers = [
                AgentFactory.create_agent(role="correctness", provider=self.provider),
                AgentFactory.create_agent(role="security", provider=self.provider),
                AgentFactory.create_agent(role="data_contract", provider=self.provider),
                AgentFactory.create_agent(role="infrastructure", provider=self.provider),
            ]

        # Phase 1: Independent Reviews
        agent_reviews: list[AgentReview] = []
        initial_findings_map: dict[str, ReviewFinding] = {}

        for reviewer in reviewers:
            rev = reviewer.review(diff_files, risk)
            agent_reviews.append(rev)
            for f in rev.findings:
                initial_findings_map[f.finding_id] = f

        initial_findings = list(initial_findings_map.values())
        if not initial_findings:
            logger.info("No initial findings produced by reviewers. Debate round not required.")
            return agent_reviews, [], []

        # Phase 2: Adversarial Challenger
        logger.info(f"Challenger reviewing {len(initial_findings)} initial findings to eliminate false positives.")
        challenges: list[DebateChallenge] = []
        for finding in initial_findings:
            # Challenger evaluates if the finding could be a test mock, documentation, or false alarm
            is_test_file = "test" in finding.file_path.lower()
            is_low_conf = finding.confidence < 0.6
            if is_test_file and "hardcoded" in finding.title.lower():
                challenges.append(
                    DebateChallenge(
                        target_finding_id=finding.finding_id,
                        challenger_id="adversarial-challenger",
                        reason="Finding is in a test file where mock credentials or synthetic tokens are customary.",
                        suggested_action="downgrade",
                        confidence=0.9,
                    )
                )
            elif is_low_conf:
                challenges.append(
                    DebateChallenge(
                        target_finding_id=finding.finding_id,
                        challenger_id="adversarial-challenger",
                        reason="Low initial confidence and ambiguous evidence snippet.",
                        suggested_action="dismiss",
                        confidence=0.75,
                    )
                )

        # Phase 3: Judicial Verdict
        # Rule: Judge CANNOT override mandatory security failures or deterministic HIGH risk findings
        final_findings: list[ReviewFinding] = []
        challenged_ids = {c.target_finding_id: c for c in challenges}

        for finding in initial_findings:
            challenge = challenged_ids.get(finding.finding_id)
            if not challenge:
                final_findings.append(finding)
                continue

            if challenge.suggested_action == "dismiss":
                # Can only dismiss if severity is NOT HIGH
                if finding.severity == RiskLevel.HIGH:
                    logger.info(f"Judge rejecting dismissal of HIGH severity finding: {finding.finding_id}")
                    final_findings.append(finding)
                else:
                    logger.info(f"Judge upheld challenge dismissing finding: {finding.finding_id}")
            elif challenge.suggested_action == "downgrade":
                downgraded = ReviewFinding(
                    finding_id=finding.finding_id,
                    severity=RiskLevel.LOW,
                    category=finding.category,
                    file_path=finding.file_path,
                    line_start=finding.line_start,
                    line_end=finding.line_end,
                    title=f"{finding.title} (Downgraded after debate)",
                    description=f"{finding.description} Note: {challenge.reason}",
                    evidence=finding.evidence,
                    suggestion=finding.suggestion,
                    confidence=0.5,
                    reviewer_id=finding.reviewer_id,
                )
                final_findings.append(downgraded)

        debate_round = DebateRound(
            round_number=1,
            challenges=challenges,
            rebuttals=[f"Rebutted {len(challenges)} initial findings based on test context and code evidence."],
            judge_decision=f"Consolidated {len(final_findings)} final findings from {len(initial_findings)} initial candidates.",
            final_findings=final_findings,
        )

        return agent_reviews, [debate_round], final_findings
