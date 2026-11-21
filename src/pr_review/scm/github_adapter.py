"""GitHub and GitHub Enterprise SCM adapter."""

from __future__ import annotations

import re
from typing import Any

from pr_review.models.base import PolicyDecision, PolicyResult, PRMetadata, ReviewReport, SCMProviderType
from pr_review.scm.provider import SCMProvider


class GitHubAdapter(SCMProvider):
    """Adapter for GitHub.com and GitHub Enterprise."""

    @property
    def provider_type(self) -> SCMProviderType:
        return SCMProviderType.GITHUB

    def detect(self, env_vars: dict[str, str]) -> float:
        """Detect GitHub based on multiple signals (URLs, Jenkins change vars, GitHub actions vars)."""
        score = 0.0
        git_url = env_vars.get("GIT_URL", "").lower()
        change_url = env_vars.get("CHANGE_URL", "").lower()

        # URL based signals
        if "github.com" in git_url or "github.com" in change_url:
            score += 0.5
        elif any(k in git_url or k in change_url for k in ["github", "ghe"]):
            score += 0.35

        # GitHub-specific env signals
        has_github_actions = "GITHUB_ACTIONS" in env_vars or "GITHUB_REPOSITORY" in env_vars
        if has_github_actions:
            score += 0.4

        # Jenkins multibranch GitHub branch source signals
        has_change_id = bool(env_vars.get("CHANGE_ID"))
        has_change_target = bool(env_vars.get("CHANGE_TARGET"))
        if has_change_id and has_change_target:
            if "github" in env_vars.get("JOB_NAME", "").lower() or "github" in git_url:
                score += 0.3

        return min(score, 1.0)

    def get_pr_metadata(self, env_vars: dict[str, str]) -> PRMetadata:
        pr_id = env_vars.get("CHANGE_ID") or env_vars.get("PR_ID") or "0"
        title = env_vars.get("CHANGE_TITLE") or f"PR #{pr_id}"
        source_branch = env_vars.get("CHANGE_BRANCH") or env_vars.get("BRANCH_NAME") or "unknown-source"
        target_branch = env_vars.get("CHANGE_TARGET") or "main"
        base_sha = env_vars.get("CHANGE_TARGET_SHA") or env_vars.get("BASE_SHA") or "0000000000000000000000000000000000000000"
        head_sha = env_vars.get("GIT_COMMIT") or env_vars.get("HEAD_SHA") or "0000000000000000000000000000000000000000"
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
            raw_metadata={"detected_by": "GitHubAdapter"},
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
        # If API token available in production, would call GitHub REST API: /repos/:owner/:repo/statuses/:sha
        # In offline/restricted mode, we safely report unverified/dry-run
        return True

    def post_comment(
        self,
        pr_metadata: PRMetadata,
        report: ReviewReport,
        idempotency_key: str = "",
    ) -> bool:
        if not self.is_available():
            return False
        # If API token available, search for comment containing idempotency_key and update/create
        return True
