"""Agent Factory for instantiating role-specific review agents."""

from __future__ import annotations

import os

from pr_review.agents.base import ReviewAgent
from pr_review.agents.claude_adapter import ClaudeReviewAdapter
from pr_review.agents.codex_adapter import CodexReviewAdapter
from pr_review.agents.offline_adapter import OfflineReviewAdapter


class AgentFactory:
    """Instantiates review agents based on role and provider configuration."""

    @staticmethod
    def create_agent(
        role: str,
        provider: str | None = None,
        agent_id: str | None = None,
        timeout: int = 120,
    ) -> ReviewAgent:
        provider = provider or os.environ.get("AI_PROVIDER", "offline").lower()
        aid = agent_id or f"{provider}-{role}"

        if provider == "codex":
            return CodexReviewAdapter(agent_id=aid, role=role, timeout=timeout)
        elif provider == "claude":
            return ClaudeReviewAdapter(agent_id=aid, role=role, timeout=timeout)
        else:
            return OfflineReviewAdapter(agent_id=aid, role=role, timeout=timeout)
