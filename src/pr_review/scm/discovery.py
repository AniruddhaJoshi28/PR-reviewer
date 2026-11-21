"""SCM Discovery and Provider Resolution module."""

from __future__ import annotations

import logging
import re
from typing import Sequence

from pr_review.models.base import SCMProviderType
from pr_review.scm.azure_adapter import AzureReposAdapter
from pr_review.scm.bitbucket_adapter import BitbucketAdapter
from pr_review.scm.generic_adapter import GenericGitAdapter
from pr_review.scm.github_adapter import GitHubAdapter
from pr_review.scm.gitlab_adapter import GitLabAdapter
from pr_review.scm.mock_adapter import MockSCMAdapter
from pr_review.scm.provider import SCMProvider

logger = logging.getLogger(__name__)


def sanitize_url(url: str) -> str:
    """Strip basic auth credentials from git/repo URLs for safe logging."""
    if not url:
        return ""
    # Matches http://user:pass@host or https://token@host
    return re.sub(r"://([^@]+)@", "://***:***@", url)


class SCMDiscovery:
    """Detects and instantiates the correct SCM provider based on multi-variable heuristics."""

    def __init__(self, providers: Sequence[SCMProvider] | None = None) -> None:
        self.providers: list[SCMProvider] = list(providers) if providers is not None else [
            MockSCMAdapter(),
            GitHubAdapter(),
            GitLabAdapter(),
            BitbucketAdapter(),
            AzureReposAdapter(),
            GenericGitAdapter(),
        ]

    def discover(self, env_vars: dict[str, str], threshold: float = 0.4) -> tuple[SCMProvider, float]:
        """Evaluate all providers and return the best matching provider and confidence score.

        If highest score is below threshold, falls back to GenericGitAdapter in provider-neutral mode.
        """
        git_url = sanitize_url(env_vars.get("GIT_URL", ""))
        logger.info(f"Initiating SCM discovery with git_url={git_url}")

        scores: list[tuple[float, SCMProvider]] = []
        for provider in self.providers:
            score = provider.detect(env_vars)
            scores.append((score, provider))
            logger.debug(f"Provider {provider.provider_type.value} scored {score:.2f}")

        # Sort descending by score
        scores.sort(key=lambda x: x[0], reverse=True)
        best_score, best_provider = scores[0]

        if best_score < threshold:
            logger.warning(
                f"Inconclusive SCM provider detection (best score: {best_score:.2f}). "
                "Defaulting to provider-neutral GenericGitAdapter."
            )
            # Find GenericGitAdapter or create one
            for p in self.providers:
                if type(p) is GenericGitAdapter:
                    return p, best_score
            return GenericGitAdapter(), best_score

        logger.info(f"Resolved SCM provider: {best_provider.provider_type.value} (score={best_score:.2f})")
        return best_provider, best_score
