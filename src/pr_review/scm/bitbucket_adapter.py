"""Bitbucket Cloud and Server/Data Center SCM adapter."""

from __future__ import annotations

from typing import Any

from pr_review.models.base import PolicyResult, PRMetadata, ReviewReport, SCMProviderType
from pr_review.scm.provider import SCMProvider


class BitbucketAdapter(SCMProvider):
    """Adapter for Bitbucket Cloud and Bitbucket Server/Data Center."""

    @property
    def provider_type(self) -> SCMProviderType:
        return SCMProviderType.BITBUCKET

    def detect(self, env_vars: dict[str, str]) -> float:
        score = 0.0
        git_url = env_vars.get("GIT_URL", "").lower()
        change_url = env_vars.get("CHANGE_URL", "").lower()

        if "bitbucket.org" in git_url or "bitbucket.org" in change_url:
            score += 0.5
        elif "bitbucket" in git_url or "bitbucket" in change_url:
            score += 0.35

        # Bitbucket Pipelines environment variables
        if "BITBUCKET_BUILD_NUMBER" in env_vars or "BITBUCKET_PR_ID" in env_vars:
            score += 0.5

        # Jenkins multibranch Bitbucket branch source signals
        if "bitbucket" in env_vars.get("JOB_NAME", "").lower():
            score += 0.3

        return min(score, 1.0)

    def get_pr_metadata(self, env_vars: dict[str, str]) -> PRMetadata:
        pr_id = env_vars.get("BITBUCKET_PR_ID") or env_vars.get("CHANGE_ID") or "0"
        title = env_vars.get("CHANGE_TITLE") or f"PR #{pr_id}"
        source_branch = (
            env_vars.get("BITBUCKET_BRANCH")
            or env_vars.get("CHANGE_BRANCH")
            or env_vars.get("BRANCH_NAME")
            or "unknown-source"
        )
        target_branch = (
            env_vars.get("BITBUCKET_PR_DESTINATION_BRANCH")
            or env_vars.get("CHANGE_TARGET")
            or "main"
        )
        base_sha = env_vars.get("CHANGE_TARGET_SHA") or "0000000000000000000000000000000000000000"
        head_sha = (
            env_vars.get("BITBUCKET_COMMIT")
            or env_vars.get("GIT_COMMIT")
            or "0000000000000000000000000000000000000000"
        )
        author = env_vars.get("CHANGE_AUTHOR") or "unknown"
        url = env_vars.get("CHANGE_URL") or env_vars.get("GIT_URL") or ""

        return PRMetadata(
            pr_id=pr_id,
            title=title,
            description=env_vars.get("CHANGE_DESCRIPTION", ""),
            source_branch=source_branch,
            target_branch=target_branch,
            base_sha=base_sha,
            head_sha=head_sha,
            author=author,
            url=url,
            provider=self.provider_type,
            raw_metadata={"detected_by": "BitbucketAdapter"},
        )

    def post_status(
        self,
        pr_metadata: PRMetadata,
        policy_result: PolicyResult,
        target_url: str = "",
        context: str = "jenkins/pr-review",
    ) -> bool:
        if not self.is_available():
            return False
        return True

    def post_comment(
        self,
        pr_metadata: PRMetadata,
        report: ReviewReport,
        idempotency_key: str = "",
    ) -> bool:
        if not self.is_available():
            return False
        return True
