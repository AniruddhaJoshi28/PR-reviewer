"""Abstract base class for all review agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pr_review.models.base import AgentReview, DiffFile, RiskClassification


class ReviewAgent(ABC):
    """Base class every review agent must implement.

    Parameters
    ----------
    agent_id:
        Unique identifier for this agent instance.
    role:
        The review role this agent fulfils (e.g. ``"correctness"``,
        ``"security"``).
    model_name:
        Name of the AI model backing this agent (``"offline"`` for
        deterministic adapters).
    timeout:
        Maximum seconds the agent may spend on a single review.
    max_tokens:
        Token budget per review call.
    cost_budget:
        Maximum USD cost allowed for a single review call.
    """

    def __init__(
        self,
        *,
        agent_id: str,
        role: str,
        model_name: str = "offline",
        timeout: int = 120,
        max_tokens: int = 4096,
        cost_budget: float = 0.50,
    ) -> None:
        self.agent_id = agent_id
        self.role = role
        self.model_name = model_name
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.cost_budget = cost_budget

    @abstractmethod
    def review(
        self,
        diff_files: list[DiffFile],
        risk: RiskClassification,
        context: dict[str, Any] | None = None,
    ) -> AgentReview:
        """Run a review over the given diff files.

        Parameters
        ----------
        diff_files:
            The files changed in this PR.
        risk:
            Pre-computed risk classification for the PR.
        context:
            Optional extra context (PR metadata, prior findings, etc.).

        Returns
        -------
        AgentReview
            Structured review output with findings and metadata.
        """

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(agent_id={self.agent_id!r}, "
            f"role={self.role!r}, model={self.model_name!r})"
        )
