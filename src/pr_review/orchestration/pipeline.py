"""Review Pipeline Orchestrator connecting all stages."""

from __future__ import annotations

import logging
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pr_review.evidence.validator import EvidenceValidator
from pr_review.models.base import (
    DiffFile,
    PolicyDecision,
    PolicyResult,
    PRMetadata,
    ReviewReport,
    RiskClassification,
    RiskLevel,
    ScanResult,
    SCMProviderType,
)
from pr_review.orchestration.debate import DebateOrchestrator
from pr_review.policy.engine import PolicyEngine
from pr_review.reporting.generator import ReportGenerator
from pr_review.risk.classifier import RiskClassifier
from pr_review.scanners.aggregate import ScannerOrchestrator
from pr_review.scm.discovery import SCMDiscovery
from pr_review.scm.mock_adapter import MockSCMAdapter
from pr_review.scm.provider import SCMProvider

logger = logging.getLogger(__name__)


class ReviewPipeline:
    """Executes the complete trusted review and evaluation pipeline."""

    def __init__(
        self,
        artifacts_dir: str = "artifacts",
        offline_demo: bool = False,
        ai_provider: str = "offline",
    ) -> None:
        self.artifacts_dir = artifacts_dir
        self.offline_demo = offline_demo
        self.ai_provider = ai_provider

        self.scm_discovery = SCMDiscovery()
        self.risk_classifier = RiskClassifier()
        self.scanner_orchestrator = ScannerOrchestrator(offline_demo=offline_demo)
        self.debate_orchestrator = DebateOrchestrator(provider=ai_provider)
        self.policy_engine = PolicyEngine()
        self.report_generator = ReportGenerator(artifacts_dir=artifacts_dir)

    def calculate_git_diff(self, base_sha: str, head_sha: str) -> list[DiffFile]:
        """Compute git diff between base and head commit in local repository."""
        diff_files: list[DiffFile] = []
        try:
            # Check git diff --name-status
            cmd = ["git", "diff", "--name-status", f"{base_sha}...{head_sha}"]
            res = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if res.returncode != 0:
                # Fallback to HEAD~1 or unstaged
                cmd = ["git", "diff", "--name-status", "HEAD~1"]
                res = subprocess.run(cmd, capture_output=True, text=True, check=False)

            if res.returncode == 0 and res.stdout.strip():
                for line in res.stdout.strip().split("\n"):
                    parts = line.split(maxsplit=1)
                    if len(parts) == 2:
                        status, file_path = parts
                        # Get patch for this file
                        patch_res = subprocess.run(
                            ["git", "diff", f"{base_sha}...{head_sha}", "--", file_path],
                            capture_output=True,
                            text=True,
                            check=False,
                        )
                        patch = patch_res.stdout if patch_res.returncode == 0 else ""
                        diff_files.append(
                            DiffFile(
                                path=file_path,
                                status=status,
                                patch=patch,
                            )
                        )
        except Exception as e:
            logger.warning(f"Could not calculate git diff: {e}")

        return diff_files

    def run_pipeline(
        self,
        env_vars: dict[str, str] | None = None,
        custom_diff: list[DiffFile] | None = None,
        custom_metadata: PRMetadata | None = None,
    ) -> ReviewReport:
        """Run all stages of the PR review pipeline."""
        env = env_vars if env_vars is not None else dict(os.environ)

        # Stage 1 & 2: SCM Discovery & Metadata
        if custom_metadata:
            pr_metadata = custom_metadata
            provider = MockSCMAdapter()
        else:
            provider, confidence = self.scm_discovery.discover(env)
            pr_metadata = provider.get_pr_metadata(env)

        logger.info(f"Target PR: #{pr_metadata.pr_id} by {pr_metadata.author} (Provider: {pr_metadata.provider.value})")

        # Stage 3: Calculate Diff
        if custom_diff is not None:
            diff_files = custom_diff
        else:
            diff_files = self.calculate_git_diff(pr_metadata.base_sha, pr_metadata.head_sha)
            if not diff_files:
                # Default synthetic diff if running without git history
                diff_files = [
                    DiffFile(
                        path="src/service/auth_manager.py",
                        status="M",
                        additions=15,
                        deletions=2,
                        patch="@@ -10,2 +10,15 @@\n+def login(username, password):\n+    query = f\"SELECT * FROM users WHERE user='{username}'\"\n+    return db.execute_raw_sql(query)\n",
                    )
                ]

        # Stage 4: Risk Classification (Deterministic)
        risk = self.risk_classifier.classify(diff_files, pr_metadata)
        logger.info(f"Deterministic risk: {risk.risk_level.value} (rules: {risk.rule_ids})")

        # Stage 5: Security Scanning
        scans = self.scanner_orchestrator.scan_all(diff_files)

        # Stage 6 & 7: Conditional AI Review & Debate
        agent_reviews, debate_rounds, raw_findings = self.debate_orchestrator.run_debate(diff_files, risk)

        # Stage 8: Evidence Validation (cross-check against diff)
        validated_findings, rejected = EvidenceValidator.validate_findings(raw_findings, diff_files)
        logger.info(f"Evidence validation: {len(validated_findings)} validated, {len(rejected)} rejected.")

        # Stage 9: Policy Evaluation
        policy_res = self.policy_engine.evaluate(
            pr_metadata=pr_metadata,
            risk_classification=risk,
            scan_results=scans,
            agent_findings=validated_findings,
            allow_mock=self.offline_demo,
        )
        logger.info(f"Policy decision: {policy_res.decision.value}")

        # Build complete Report
        report = ReviewReport(
            pr_metadata=pr_metadata,
            risk_classification=risk,
            scan_results=scans,
            agent_reviews=agent_reviews,
            debate_rounds=debate_rounds,
            policy_result=policy_res,
            generated_at=datetime.now(timezone.utc),
            pipeline_version="1.0.0",
        )

        # Stage 10: Generate all 5 artifacts
        self.report_generator.generate_all(report)

        # Stage 11: Remote SCM feedback (if available and authorized)
        if provider.is_available() and not self.offline_demo:
            try:
                provider.post_status(pr_metadata, policy_res)
                provider.post_comment(pr_metadata, report, idempotency_key=f"pr-{pr_metadata.pr_id}")
            except Exception as e:
                logger.warning(f"SCM feedback failed (continuing provider-neutral): {e}")

        return report

    def run_offline_demo(self) -> ReviewReport:
        """Run an offline demonstration with realistic synthetic PR changes."""
        logger.info("Initializing offline demonstration pipeline.")
        mock_metadata = PRMetadata(
            pr_id="101",
            title="Update user authentication and checkout flow",
            description="Adds session token validation and dynamic SQL logging.",
            source_branch="feature/auth-v2",
            target_branch="main",
            base_sha="1111111111111111111111111111111111111111",
            head_sha="2222222222222222222222222222222222222222",
            author="demo-developer",
            url="https://github.com/AniruddhaJoshi28/PR-reviewer/pull/101",
            provider=SCMProviderType.GITHUB,
            raw_metadata={"demo": True},
        )

        mock_diff = [
            DiffFile(
                path="src/auth/service.py",
                status="M",
                additions=12,
                deletions=1,
                patch="""@@ -4,1 +4,12 @@
-def check_token(t):
+def check_token(t):
+    # Hardcoded test fallback token
+    AWS_SECRET_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
+    return t == "secret"
+
+def get_user(uid):
+    query = f"SELECT * FROM users WHERE id = '{uid}'"
+    return db.execute_raw_sql(query)
""",
            ),
            DiffFile(
                path="docs/auth_architecture.md",
                status="M",
                additions=5,
                deletions=0,
                patch="""@@ -1,3 +1,8 @@
+# Authentication Guide
+This document outlines user auth flows.
""",
            ),
        ]

        return self.run_pipeline(
            env_vars={"OFFLINE_DEMO": "1"},
            custom_diff=mock_diff,
            custom_metadata=mock_metadata,
        )
