"""Contract tests for all SCM adapters."""

import pytest
from pr_review.models.base import PolicyDecision, PolicyResult, PRMetadata, RiskLevel, SCMProviderType
from pr_review.scm.azure_adapter import AzureReposAdapter
from pr_review.scm.bitbucket_adapter import BitbucketAdapter
from pr_review.scm.generic_adapter import GenericGitAdapter
from pr_review.scm.github_adapter import GitHubAdapter
from pr_review.scm.gitlab_adapter import GitLabAdapter
from pr_review.scm.mock_adapter import MockSCMAdapter
from pr_review.scm.provider import SCMProvider


@pytest.mark.parametrize(
    "adapter_cls,expected_type",
    [
        (GitHubAdapter, SCMProviderType.GITHUB),
        (GitLabAdapter, SCMProviderType.GITLAB),
        (BitbucketAdapter, SCMProviderType.BITBUCKET),
        (AzureReposAdapter, SCMProviderType.AZURE_DEVOPS),
        (GenericGitAdapter, SCMProviderType.GENERIC_GIT),
        (MockSCMAdapter, SCMProviderType.GENERIC_GIT),
    ],
)
def test_scm_adapter_contracts(adapter_cls, expected_type):
    adapter: SCMProvider = adapter_cls()
    assert adapter.provider_type == expected_type

    # Test detection contract
    score = adapter.detect({})
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0

    # Test get_pr_metadata contract
    meta = adapter.get_pr_metadata({"CHANGE_ID": "123", "GIT_COMMIT": "abc"})
    assert isinstance(meta, PRMetadata)
    assert meta.pr_id in ("123", "generic-1", "42")

    # Test post_status contract (safe in offline mode)
    policy_res = PolicyResult(
        decision=PolicyDecision.PASS,
        risk_level=RiskLevel.LOW,
        mandatory_checks_passed=True,
    )
    status_success = adapter.post_status(meta, policy_res)
    assert isinstance(status_success, bool)
