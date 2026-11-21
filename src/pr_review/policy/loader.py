"""Policy configuration loader and schema validation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


def load_policy_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load policy.yaml from path or default location."""
    if config_path is None:
        # Default to repo root config/policy.yaml
        candidates = [
            Path("config/policy.yaml"),
            Path(__file__).resolve().parents[3] / "config" / "policy.yaml",
        ]
        for c in candidates:
            if c.exists():
                config_path = c
                break

    if not config_path or not Path(config_path).exists():
        # Fallback default configuration
        return {
            "version": "1.0.0",
            "mandatory_checks": [
                {"scanner": "semgrep", "must_pass": True},
                {"scanner": "gitleaks", "must_pass": True},
            ],
            "approval_requirements": {
                "high": {"min_approvers": 2, "require_security_team": True, "auto_merge": False},
                "medium": {"min_approvers": 1, "require_security_team": False, "auto_merge": False},
                "low": {"min_approvers": 0, "require_security_team": False, "auto_merge": False},
            },
        }

    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}
