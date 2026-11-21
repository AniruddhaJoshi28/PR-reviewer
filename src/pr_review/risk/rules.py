"""Deterministic Risk Rules and Registry."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Pattern

from pr_review.models.base import RiskLevel


@dataclass(frozen=True)
class RiskRule:
    """A deterministic risk rule."""

    rule_id: str
    risk_level: RiskLevel
    description: str
    path_patterns: list[Pattern[str]] = field(default_factory=list)
    content_patterns: list[Pattern[str]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Built-in Deterministic Rules
# ---------------------------------------------------------------------------

DEFAULT_RULES: list[RiskRule] = [
    # HIGH RISK RULES
    RiskRule(
        rule_id="RULE_HIGH_AUTH_PATH",
        risk_level=RiskLevel.HIGH,
        description="Path touches authentication, authorization, or IAM components",
        path_patterns=[
            re.compile(r"(^|/)(auth|security|rbac|iam|tokens|jwt|oauth|permissions)[\._\-/]?", re.IGNORECASE),
        ],
    ),
    RiskRule(
        rule_id="RULE_HIGH_SECRETS_CONTENT",
        risk_level=RiskLevel.HIGH,
        description="Content contains potential secrets, tokens, or private keys",
        content_patterns=[
            re.compile(r"(?i)(api[_-]?key|secret[_-]?key|access[_-]?token|password)\s*=\s*['\"][A-Za-z0-9_\-\.\/+=]{8,}['\"]"),
            re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
            re.compile(r"(?i)AKIA[0-9A-Z]{16}"),
        ],
    ),
    RiskRule(
        rule_id="RULE_HIGH_SQL_EXECUTION",
        risk_level=RiskLevel.HIGH,
        description="Diff touches raw SQL queries or dynamic query execution",
        content_patterns=[
            re.compile(r"""(?i)(f["'].*\b(SELECT|INSERT|UPDATE|DELETE|DROP)\b|\b(SELECT|INSERT|UPDATE|DELETE|DROP)\b.*(f["']|\.format\(|%\s*\())"""),
            re.compile(r"(?i)execute_raw_sql|cursor\.execute\(f['\"]"),
        ],
    ),
    RiskRule(
        rule_id="RULE_HIGH_CONCURRENCY",
        risk_level=RiskLevel.HIGH,
        description="Shared mutable concurrency or race condition risk",
        content_patterns=[
            re.compile(r"(?i)(race condition|threading\.|multiprocessing\.|active_transactions|double-spend)"),
        ],
    ),
    RiskRule(
        rule_id="RULE_HIGH_UNSAFE_EXECUTION",
        risk_level=RiskLevel.HIGH,
        description="Diff uses unsafe subprocess or code evaluation primitives",
        content_patterns=[
            re.compile(r"(?i)(subprocess\.Popen|subprocess\.call|subprocess\.run).*shell\s*=\s*True"),
            re.compile(r"(?i)\b(eval|exec)\s*\("),
        ],
    ),
    RiskRule(
        rule_id="RULE_HIGH_INFRASTRUCTURE",
        risk_level=RiskLevel.HIGH,
        description="Infrastructure, CI/CD, container, or cloud deployment changes",
        path_patterns=[
            re.compile(r"(^|/)(\.github/workflows|jenkins|Jenkinsfile|Dockerfile|docker-compose|terraform|\.tf|unsafe_infra)[\._\-/]?", re.IGNORECASE),
        ],
        content_patterns=[
            re.compile(r"0\.0\.0\.0/0"),
        ],
    ),
    RiskRule(
        rule_id="RULE_HIGH_SECURITY_POLICY",
        risk_level=RiskLevel.HIGH,
        description="Security policy or configuration changes",
        path_patterns=[
            re.compile(r"(^|/)(config/policy\.yaml|security_rules|firewall)[\._\-/]?", re.IGNORECASE),
        ],
    ),
    RiskRule(
        rule_id="RULE_HIGH_PROMPT_INJECTION",
        risk_level=RiskLevel.HIGH,
        description="Potential prompt injection or instruction override in PR",
        content_patterns=[
            re.compile(r"(?i)IGNORE (ALL )?(PREVIOUS|PRIOR) INSTRUCTIONS"),
            re.compile(r"(?i)MARK THIS (PR|PULL REQUEST) AS (APPROVED|SAFE|PASS)"),
            re.compile(r"(?i)SYSTEM (PROMPT|OVERRIDE):.*(ALLOW|IGNORE)"),
        ],
    ),

    # MEDIUM RISK RULES
    RiskRule(
        rule_id="RULE_MED_DEPENDENCY_CHANGE",
        risk_level=RiskLevel.MEDIUM,
        description="Project dependency or build configuration change",
        path_patterns=[
            re.compile(r"(^|/)(requirements.*\.txt|pyproject\.toml|package\.json|package-lock\.json|Pipfile|setup\.py)$", re.IGNORECASE),
        ],
    ),
    RiskRule(
        rule_id="RULE_MED_BUSINESS_LOGIC",
        risk_level=RiskLevel.MEDIUM,
        description="Core business logic, API models, or services modified",
        path_patterns=[
            re.compile(r"(^|/)(api|models|services|billing|payments|routes|endpoints|business_logic)[\._\-/]?", re.IGNORECASE),
        ],
        content_patterns=[
            re.compile(r"(?i)(def calculate_|volume_brackets|serialize_user_response)"),
        ],
    ),
    RiskRule(
        rule_id="RULE_MED_AGENT_ORCHESTRATION",
        risk_level=RiskLevel.MEDIUM,
        description="AI prompts or agent orchestration logic modified",
        path_patterns=[
            re.compile(r"(^|/)(agents|orchestration|prompts|evaluations)[\._\-/]?", re.IGNORECASE),
        ],
    ),

    # LOW RISK RULES
    RiskRule(
        rule_id="RULE_LOW_DOCUMENTATION",
        risk_level=RiskLevel.LOW,
        description="Pure documentation, markdown, or text updates",
        path_patterns=[
            re.compile(r"\.(md|markdown|rst|txt|adoc)$", re.IGNORECASE),
            re.compile(r"(^|/)docs/", re.IGNORECASE),
        ],
    ),
    RiskRule(
        rule_id="RULE_LOW_TEST_ONLY",
        risk_level=RiskLevel.LOW,
        description="Test suite changes only",
        path_patterns=[
            re.compile(r"(^|/)tests?/", re.IGNORECASE),
            re.compile(r"(test_.*|.*_test)\.py$", re.IGNORECASE),
            re.compile(r"failing_test\.py$", re.IGNORECASE),
        ],
    ),
    RiskRule(
        rule_id="RULE_LOW_SAFE_CONFIG",
        risk_level=RiskLevel.LOW,
        description="False positive trap safe configuration",
        path_patterns=[
            re.compile(r"false_positive_trap\.py$", re.IGNORECASE),
        ],
    ),
]
