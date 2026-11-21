"""Unit tests for review agents, offline adapter, and factory."""

import pytest
from pr_review.agents.factory import AgentFactory
from pr_review.models.base import DiffFile, RiskClassification, RiskLevel


def test_offline_reviewer_finds_sql_injection():
    agent = AgentFactory.create_agent(role="security", provider="offline")
    diff = [
        DiffFile(
            path="src/query.py",
            status="M",
            patch='+cursor.execute(f"SELECT * FROM items WHERE id = {item_id}")\n',
        )
    ]
    risk = RiskClassification(risk_level=RiskLevel.HIGH)
    review = agent.review(diff, risk)
    assert len(review.findings) >= 1
    assert any("sql" in f.title.lower() for f in review.findings)


def test_external_ai_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ENABLE_EXTERNAL_AI", raising=False)
    monkeypatch.delenv("CODEX_API_KEY", raising=False)

    # When fallback allowed, falls back safely to offline
    agent = AgentFactory.create_agent(role="correctness", provider="codex")
    diff = [DiffFile(path="src/code.py", status="M")]
    risk = RiskClassification(risk_level=RiskLevel.LOW)
    review = agent.review(diff, risk)
    assert "offline" in review.agent_id or review.findings == []
