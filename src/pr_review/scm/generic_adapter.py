"""Generic Git SCM adapter (fallback for on-prem or unknown Git hosts)."""

from __future__ import annotations

from typing import Any

from pr_review.models.base import PolicyResult, PRMetadata, ReviewReport, SCMProviderType
from pr_review.scm.provider import SCMProvider


class GenericGitAdapter(SCMProvider):
    """Adapter for generic Git repositories without dedicated API integration."""

    @property
    def provider_type(self) -> SCMProviderType:
        return SCMProviderType.GENERIC_GIT

    def detect(self, env_vars: dict[str, str]) -> float:
        # Matches any Git environment with a GIT_URL or GIT_COMMIT, but lower base confidence
        git_url = env_vars.get("GIT_URL", "")
        git_commit = env_vars.get("GIT_COMMIT", "")
        if git_url or git_commit:
            return 0.2
        return 0.1

    def get_pr_metadata(self, env_vars: dict[str, str]) -> PRMetadata:
        pr_id = env_vars.get("CHANGE_ID") or "generic-1"
        title = env_vars.get("CHANGE_TITLE") or f"Generic Change #{pr_id}"
        source_branch = env_vars.get("CHANGE_BRANCH") or env_vars.get("BRANCH_NAME") or "HEAD"
        target_branch = env_vars.get("CHANGE_TARGET") or "main"
        base_sha = env_vars.get("CHANGE_TARGET_SHA") or "0000000000000000000000000000000000000000"
        head_sha = env_vars.get("GIT_COMMIT") or "0000000000000000000000000000000000000000"
        author = env_vars.get("CHANGE_AUTHOR") or "git-user"
        url = env_vars.get("GIT_URL", "")

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
            raw_metadata={"detected_by": "GenericGitAdapter", "mode": "provider_neutral"},
        )

    def post_status(
        self,
        pr_metadata: PRMetadata,
        policy_result: PolicyResult,
        target_url: str = "",
        context: str = "jenkins/pr-review",
    ) -> bool:
        # In generic mode, remote publishing is unavailable
        return False

    def post_comment(
        self,
        pr_metadata: PRMetadata,
        report: ReviewReport,
        idempotency_key: str = "",
    ) -> bool:
        # In generic mode, remote comments are unavailable
        return False
