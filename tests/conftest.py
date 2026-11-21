"""Shared pytest fixtures and test configurations."""

from __future__ import annotations

import os
import pytest

from pr_review.models.base import DiffFile, PRMetadata, RiskClassification, RiskLevel, SCMProviderType


@pytest.fixture
def sample_metadata() -> PRMetadata:
    return PRMetadata(
        pr_id="42",
        title="Add user authentication and billing integration",
        description="Implements token-based session auth.",
        source_branch="feature/auth",
        target_branch="main",
        base_sha="1111111111111111111111111111111111111111",
        head_sha="2222222222222222222222222222222222222222",
        author="alice",
        url="https://github.com/AniruddhaJoshi28/PR-reviewer/pull/42",
        provider=SCMProviderType.GITHUB,
    )


@pytest.fixture
def high_risk_diff() -> list[DiffFile]:
    return [
        DiffFile(
            path="src/auth/service.py",
            status="M",
            additions=10,
            deletions=2,
            patch="""@@ -1,5 +1,10 @@
+def login(user, password):
+    AWS_SECRET_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
+    query = f"SELECT * FROM users WHERE user='{user}'"
+    return db.execute(query)
""",
        )
    ]


@pytest.fixture
def low_risk_diff() -> list[DiffFile]:
    return [
        DiffFile(
            path="docs/index.md",
            status="M",
            additions=3,
            deletions=1,
            patch="""@@ -1,2 +1,3 @@
-# Documentation
+# PR Review Documentation
""",
        )
    ]
