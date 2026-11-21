"""GitLab SCM adapter."""

from __future__ import annotations

from typing import Any

from pr_review.models.base import PolicyResult, PRMetadata, ReviewReport, SCMProviderType
from pr_review.scm.provider import SCMProvider


class GitLabAdapter(SCMProvider):
    """Adapter for GitLab.com and self-managed GitLab."""

    @property
    def provider_type(self) -> SCMProviderType:
        return SCMProviderType.GITLAB

    def detect(self, env_vars: dict[str, str]) -> float:
        score = 0.0
        git_url = env_vars.get("GIT_URL", "").lower()
        change_url = env_vars.get("CHANGE_URL", "").lower()

        if "gitlab.com" in git_url or "gitlab.com" in change_url:
            score += 0.5
        elif "gitlab" in git_url or "gitlab" in change_url:
            score += 0.35

        # GitLab CI environment variables
        if "GITLAB_CI" in env_vars or "CI_MERGE_REQUEST_IID" in env_vars:
            score += 0.5

        # Jenkins multibranch GitLab branch source signals
        if env_vars.get("gitlabMergeRequestIid") or "gitlab" in env_vars.get("JOB_NAME", "").lower():
            score += 0.3

        return min(score, 1.0)

    def get_pr_metadata(self, env_vars: dict[str, str]) -> PRMetadata:
        pr_id = (
            env_vars.get("CI_MERGE_REQUEST_IID")
            or env_vars.get("gitlabMergeRequestIid")
            or env_vars.get("CHANGE_ID")
            or "0"
        )
        title = env_vars.get("CI_MERGE_REQUEST_TITLE") or env_vars.get("CHANGE_TITLE") or f"MR !{pr_id}"
        source_branch = (
            env_vars.get("CI_MERGE_REQUEST_SOURCE_BRANCH_NAME")
            or env_vars.get("CHANGE_BRANCH")
            or env_vars.get("BRANCH_NAME")
            or "unknown-source"
        )
        target_branch = (
            env_vars.get("CI_MERGE_REQUEST_TARGET_BRANCH_NAME")
            or env_vars.get("CHANGE_TARGET")
            or "main"
        )
        base_sha = (
            env_vars.get("CI_MERGE_REQUEST_DIFF_BASE_SHA")
            or env_vars.get("CHANGE_TARGET_SHA")
            or "0000000000000000000000000000000000000000"
        )
        head_sha = (
            env_vars.get("CI_COMMIT_SHA")
            or env_vars.get("GIT_COMMIT")
            or "0000000000000000000000000000000000000000"
        )
        author = env_vars.get("GITLAB_USER_LOGIN") or env_vars.get("CHANGE_AUTHOR") or "unknown"
        url = env_vars.get("CI_MERGE_REQUEST_PROJECT_URL") or env_vars.get("CHANGE_URL") or ""

        return PRMetadata(
            pr_id=pr_id,
            title=title,
            description=env_vars.get("CI_MERGE_REQUEST_DESCRIPTION") or env_vars.get("CHANGE_DESCRIPTION", ""),
            source_branch=source_branch,
            target_branch=target_branch,
            base_sha=base_sha,
            head_sha=head_sha,
            author=author,
            url=url,
            provider=self.provider_type,
            raw_metadata={"detected_by": "GitLabAdapter"},
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
