"""SCM Provider interface and base classes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pr_review.models.base import PolicyResult, PRMetadata, ReviewReport, SCMProviderType


class SCMProvider(ABC):
    """Abstract base class for Git SCM providers."""

    def __init__(self, token: str | None = None, base_url: str | None = None) -> None:
        self.token = token
        self.base_url = base_url

    @property
    @abstractmethod
    def provider_type(self) -> SCMProviderType:
        """Return the SCM provider type."""
        ...

    @abstractmethod
    def detect(self, env_vars: dict[str, str]) -> float:
        """Score confidence that this provider matches the environment (0.0 to 1.0).

        Must NOT rely on a single environment variable alone.
        """
        ...

    @abstractmethod
    def get_pr_metadata(self, env_vars: dict[str, str]) -> PRMetadata:
        """Extract normalized PR metadata from environment and/or API."""
        ...

    @abstractmethod
    def post_status(
        self,
        pr_metadata: PRMetadata,
        policy_result: PolicyResult,
        target_url: str = "",
        context: str = "jenkins/pr-review",
    ) -> bool:
        """Post a commit status check to the SCM provider.

        Returns True if successful, False if provider is unavailable or read-only.
        """
        ...

    @abstractmethod
    def post_comment(
        self,
        pr_metadata: PRMetadata,
        report: ReviewReport,
        idempotency_key: str = "",
    ) -> bool:
        """Post or update an idempotent summary review comment on the PR.

        Returns True if posted/updated, False otherwise.
        """
        ...

    def is_available(self) -> bool:
        """Check if provider credentials/network are configured and usable."""
        return bool(self.token)
