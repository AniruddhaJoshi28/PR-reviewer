"""Mock SCM adapter for offline local testing and demonstrations."""

from __future__ import annotations

from typing import Any

from pr_review.models.base import PolicyResult, PRMetadata, ReviewReport, SCMProviderType
from pr_review.scm.provider import SCMProvider


class MockSCMAdapter(SCMProvider):
    """Mock adapter returning deterministic synthetic PR data for offline mode."""

    def __init__(
        self,
        pr_id: str = "42",
        title: str = "Enterprise feature update (Mock PR)",
        author: str = "offline-dev",
        source_branch: str = "feature/payment-v2",
        target_branch: str = "main",
        base_sha: str = "a1b2c3d4e5f67890123456789012345678901234",
        head_sha: str = "f6e5d4c3b2a10987654321098765432109876543",
    ) -> None:
        super().__init__(token="mock-token-offline")
        self.pr_id = pr_id
        self.title = title
        self.author = author
        self.source_branch = source_branch
        self.target_branch = target_branch
        self.base_sha = base_sha
        self.head_sha = head_sha
        self.statuses_posted: list[dict[str, Any]] = []
        self.comments_posted: list[dict[str, Any]] = []

    @property
    def provider_type(self) -> SCMProviderType:
        return SCMProviderType.GENERIC_GIT

    def detect(self, env_vars: dict[str, str]) -> float:
        if env_vars.get("OFFLINE_DEMO") == "1" or env_vars.get("MOCK_SCM") == "1":
            return 1.0
        return 0.0

    def get_pr_metadata(self, env_vars: dict[str, str]) -> PRMetadata:
        return PRMetadata(
            pr_id=self.pr_id,
            title=self.title,
            description="Synthetic PR for offline demonstration and testing.",
            source_branch=self.source_branch,
            target_branch=self.target_branch,
            base_sha=self.base_sha,
            head_sha=self.head_sha,
            author=self.author,
            url="http://mock-scm.local/repo/pull/42",
            provider=self.provider_type,
            raw_metadata={"mode": "mock_offline", "is_mock": True},
        )

    def post_status(
        self,
        pr_metadata: PRMetadata,
        policy_result: PolicyResult,
        target_url: str = "",
        context: str = "jenkins/pr-review",
    ) -> bool:
        if pr_metadata is None or policy_result is None:
            return False
        self.statuses_posted.append({
            "pr_id": pr_metadata.pr_id,
            "decision": policy_result.decision.value,
            "context": context,
            "target_url": target_url,
        })
        return True

    def post_comment(
        self,
        pr_metadata: PRMetadata,
        report: ReviewReport,
        idempotency_key: str = "",
    ) -> bool:
        if pr_metadata is None or report is None:
            return False
        self.comments_posted.append({
            "pr_id": pr_metadata.pr_id,
            "idempotency_key": idempotency_key,
            "policy": report.policy_result.decision.value if report.policy_result else "UNKNOWN",
        })
        return True
