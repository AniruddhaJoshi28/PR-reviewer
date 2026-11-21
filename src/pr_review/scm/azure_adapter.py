"""Azure DevOps Repos SCM adapter."""

from __future__ import annotations

from typing import Any

from pr_review.models.base import PolicyResult, PRMetadata, ReviewReport, SCMProviderType
from pr_review.scm.provider import SCMProvider


class AzureReposAdapter(SCMProvider):
    """Adapter for Azure DevOps Repos."""

    @property
    def provider_type(self) -> SCMProviderType:
        return SCMProviderType.AZURE_DEVOPS

    def detect(self, env_vars: dict[str, str]) -> float:
        score = 0.0
        git_url = env_vars.get("GIT_URL", "").lower()
        change_url = env_vars.get("CHANGE_URL", "").lower()

        if "dev.azure.com" in git_url or "visualstudio.com" in git_url:
            score += 0.5
        if "dev.azure.com" in change_url or "visualstudio.com" in change_url:
            score += 0.5

        # Azure Pipelines environment variables
        if "TF_BUILD" in env_vars or "BUILD_REPOSITORY_URI" in env_vars:
            score += 0.4

        # Jenkins job naming conventions
        if "azure" in env_vars.get("JOB_NAME", "").lower():
            score += 0.2

        return min(score, 1.0)

    def get_pr_metadata(self, env_vars: dict[str, str]) -> PRMetadata:
        pr_id = (
            env_vars.get("SYSTEM_PULLREQUEST_PULLREQUESTID")
            or env_vars.get("CHANGE_ID")
            or "0"
        )
        title = env_vars.get("CHANGE_TITLE") or f"PR #{pr_id}"
        source_branch = (
            env_vars.get("SYSTEM_PULLREQUEST_SOURCEBRANCH")
            or env_vars.get("CHANGE_BRANCH")
            or env_vars.get("BRANCH_NAME")
            or "unknown-source"
        )
        target_branch = (
            env_vars.get("SYSTEM_PULLREQUEST_TARGETBRANCH")
            or env_vars.get("CHANGE_TARGET")
            or "main"
        )
        base_sha = env_vars.get("CHANGE_TARGET_SHA") or "0000000000000000000000000000000000000000"
        head_sha = (
            env_vars.get("BUILD_SOURCEVERSION")
            or env_vars.get("GIT_COMMIT")
            or "0000000000000000000000000000000000000000"
        )
        author = env_vars.get("BUILD_REQUESTEDFOR") or env_vars.get("CHANGE_AUTHOR") or "unknown"
        url = env_vars.get("CHANGE_URL") or env_vars.get("BUILD_REPOSITORY_URI") or ""

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
            raw_metadata={"detected_by": "AzureReposAdapter"},
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
