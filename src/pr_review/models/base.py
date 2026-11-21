"""Core Pydantic v2 models for the PR review pipeline."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class RiskLevel(str, Enum):
    """Risk classification levels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class PolicyDecision(str, Enum):
    """Possible policy gate decisions."""

    PASS = "PASS"
    BLOCKED = "BLOCKED"
    HUMAN_APPROVAL_REQUIRED = "HUMAN_APPROVAL_REQUIRED"
    INCOMPLETE = "INCOMPLETE"


class SCMProviderType(str, Enum):
    """Supported SCM provider types."""

    GITHUB = "GITHUB"
    GITLAB = "GITLAB"
    BITBUCKET = "BITBUCKET"
    AZURE_DEVOPS = "AZURE_DEVOPS"
    GENERIC_GIT = "GENERIC_GIT"
    UNKNOWN = "UNKNOWN"


class ScanStatus(str, Enum):
    """Detailed status of a security or quality scanner execution."""

    PASS = "PASS"
    FAIL = "FAIL"
    NOT_RUN = "NOT_RUN"
    ERROR = "ERROR"
    MOCK_PASS = "MOCK_PASS"
    MOCK_FAIL = "MOCK_FAIL"


# ---------------------------------------------------------------------------
# Diff & PR metadata
# ---------------------------------------------------------------------------


class DiffFile(BaseModel):
    """Represents a single file in a PR diff."""

    model_config = ConfigDict(frozen=True)

    path: str
    old_path: str | None = None
    status: str  # added, modified, deleted, renamed
    additions: int = 0
    deletions: int = 0
    patch: str | None = None
    is_binary: bool = False


class PRMetadata(BaseModel):
    """Metadata about a pull request."""

    model_config = ConfigDict(frozen=True)

    pr_id: str
    title: str
    description: str = ""
    source_branch: str
    target_branch: str
    base_sha: str
    head_sha: str
    author: str
    url: str = ""
    provider: SCMProviderType = SCMProviderType.UNKNOWN
    raw_metadata: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Risk & scanning
# ---------------------------------------------------------------------------


class RiskClassification(BaseModel):
    """Result of risk classification for a PR."""

    model_config = ConfigDict(frozen=True)

    risk_level: RiskLevel
    rule_ids: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    affected_files: list[str] = Field(default_factory=list)
    reasoning_summary: str = ""
    policy_version: str = ""


class ScanResult(BaseModel):
    """Result from a single security / quality scanner."""

    model_config = ConfigDict(frozen=True)

    scanner_name: str
    status: ScanStatus = ScanStatus.NOT_RUN
    passed: bool = False
    is_mock: bool = False
    findings: list[dict[str, Any]] = Field(default_factory=list)
    sarif_path: str | None = None
    error_message: str | None = None
    execution_time_seconds: float = 0.0


# ---------------------------------------------------------------------------
# Review findings & agent output
# ---------------------------------------------------------------------------


class ReviewFinding(BaseModel):
    """A single finding produced by a review agent."""

    model_config = ConfigDict(frozen=True)

    finding_id: str
    severity: RiskLevel
    category: str
    file_path: str
    line_start: int | None = None
    line_end: int | None = None
    title: str
    description: str
    evidence: str = ""
    suggestion: str = ""
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    reviewer_id: str = ""


class AgentReview(BaseModel):
    """Complete review output from a single AI agent."""

    model_config = ConfigDict(frozen=True)

    agent_id: str
    agent_role: str
    findings: list[ReviewFinding] = Field(default_factory=list)
    summary: str = ""
    risk_assessment: RiskLevel | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    model_name: str = ""
    token_usage: int = 0
    latency_seconds: float = 0.0


# ---------------------------------------------------------------------------
# Debate
# ---------------------------------------------------------------------------


class DebateChallenge(BaseModel):
    """A challenge against an initial finding during debate."""

    model_config = ConfigDict(frozen=True)

    target_finding_id: str
    challenger_id: str
    reason: str
    suggested_action: str  # dismiss, downgrade, confirm
    confidence: float = 1.0


class DebateRound(BaseModel):
    """A single round in the adversarial debate between agents."""

    model_config = ConfigDict(frozen=True)

    round_number: int
    challenges: list[DebateChallenge] = Field(default_factory=list)
    rebuttals: list[str] = Field(default_factory=list)
    judge_decision: str = ""
    final_findings: list[ReviewFinding] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Policy
# ---------------------------------------------------------------------------


class PolicyResult(BaseModel):
    """Result of evaluating the policy gate."""

    model_config = ConfigDict(frozen=True)

    decision: PolicyDecision
    risk_level: RiskLevel
    mandatory_checks_passed: bool
    reasons: list[str] = Field(default_factory=list)
    human_approvers: list[str] = Field(default_factory=list)
    override_info: dict[str, Any] = Field(default_factory=dict)
    policy_version: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Top-level report
# ---------------------------------------------------------------------------


class ReviewReport(BaseModel):
    """Complete review report aggregating all pipeline outputs."""

    model_config = ConfigDict(frozen=True)

    pr_metadata: PRMetadata
    risk_classification: RiskClassification
    scan_results: list[ScanResult] = Field(default_factory=list)
    agent_reviews: list[AgentReview] = Field(default_factory=list)
    debate_rounds: list[DebateRound] = Field(default_factory=list)
    policy_result: PolicyResult | None = None
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    pipeline_version: str = "1.0.0"


# ---------------------------------------------------------------------------
# Evaluation metrics
# ---------------------------------------------------------------------------


class EvaluationMetrics(BaseModel):
    """Metrics for evaluating the review pipeline's accuracy."""

    model_config = ConfigDict(frozen=True)

    benchmark_name: str = "default"
    total_fixtures: int = 0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    severity_weighted_recall: float = 0.0
    false_positive_rate: float = 0.0
    high_risk_false_negatives: int = 0
    hallucinated_findings: int = 0
    evidence_validity_rate: float = 0.0
    mean_latency_seconds: float = 0.0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
