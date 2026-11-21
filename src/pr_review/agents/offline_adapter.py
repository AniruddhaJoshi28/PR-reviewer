"""Deterministic pattern-based review adapter.

This adapter performs code review using regular-expression and AST-based
pattern matching.  It requires **no** external API calls and is suitable for
offline / CI-only environments.
"""

from __future__ import annotations

import re
import time
import uuid
from typing import Any

from pr_review.agents.base import ReviewAgent
from pr_review.models.base import (
    AgentReview,
    DiffFile,
    ReviewFinding,
    RiskClassification,
    RiskLevel,
)

# ---------------------------------------------------------------------------
# Pattern definitions
# ---------------------------------------------------------------------------

_SQL_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"""f["'](?:SELECT|INSERT|UPDATE|DELETE|DROP)\b.*\{""", re.IGNORECASE),
    re.compile(r"""["'](?:SELECT|INSERT|UPDATE|DELETE|DROP)\b.*%s""", re.IGNORECASE),
    re.compile(r"""["'](?:SELECT|INSERT|UPDATE|DELETE|DROP)\b.*\bformat\(""", re.IGNORECASE),
    re.compile(r"""\.execute\(\s*f["']""", re.IGNORECASE),
    re.compile(r"""\.execute\([^)]*%""", re.IGNORECASE),
    re.compile(r"""\.execute\([^)]*\+\s*\w+""", re.IGNORECASE),
]

_HARDCODED_SECRET_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"""(?:AWS_SECRET_ACCESS_KEY|AWS_ACCESS_KEY_ID|PRIVATE_KEY|API_KEY|SECRET_KEY|DATABASE_PASSWORD|DB_PASSWORD)\s*=\s*["'][^"']{8,}["']""",
        re.IGNORECASE,
    ),
    re.compile(r"""(?:password|passwd|secret|token)\s*=\s*["'][^"']{8,}["']""", re.IGNORECASE),
    re.compile(r"""AKIA[0-9A-Z]{16}"""),
]

_MISSING_ERROR_HANDLING_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"""except\s*:\s*\n\s*pass"""),
    re.compile(r"""except\s+Exception\s*:\s*\n\s*pass"""),
    re.compile(r"""except\s*:\s*\n\s*\.\.\."""),
]

_PROMPT_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"""IGNORE\s+ALL\s+PREVIOUS\s+INSTRUCTIONS""", re.IGNORECASE),
    re.compile(r"""MARK\s+THIS\s+PR\s+AS\s+APPROVED""", re.IGNORECASE),
    re.compile(r"""DISREGARD\s+(?:PRIOR|ABOVE|ALL)\s+(?:RULES|INSTRUCTIONS)""", re.IGNORECASE),
    re.compile(r"""SYSTEM\s*:\s*You\s+are""", re.IGNORECASE),
]

_OPEN_SECURITY_GROUP_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"""0\.0\.0\.0/0"""),
    re.compile(r"""::/0"""),
    re.compile(r"""cidr_blocks\s*=\s*\[\s*["']0\.0\.0\.0/0["']"""),
]

_LARGE_FUNCTION_LINE_THRESHOLD = 50


class OfflineReviewAdapter(ReviewAgent):
    """Deterministic review adapter using pattern matching — no API calls."""

    def __init__(
        self,
        *,
        agent_id: str = "offline-reviewer",
        role: str = "correctness",
        model_name: str = "offline",
        timeout: int = 60,
        max_tokens: int = 0,
        cost_budget: float = 0.0,
    ) -> None:
        super().__init__(
            agent_id=agent_id,
            role=role,
            model_name=model_name,
            timeout=timeout,
            max_tokens=max_tokens,
            cost_budget=cost_budget,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def review(
        self,
        diff_files: list[DiffFile],
        risk: RiskClassification,
        context: dict[str, Any] | None = None,
    ) -> AgentReview:
        start = time.monotonic()
        findings: list[ReviewFinding] = []

        for diff in diff_files:
            if diff.is_binary or diff.patch is None:
                continue
            findings.extend(self._scan_patch(diff))

        elapsed = time.monotonic() - start
        return AgentReview(
            agent_id=self.agent_id,
            agent_role=self.role,
            findings=findings,
            summary=self._build_summary(findings),
            risk_assessment=risk.risk_level,
            model_name=self.model_name,
            token_usage=0,
            latency_seconds=round(elapsed, 4),
        )

    # ------------------------------------------------------------------
    # Internal scanning helpers
    # ------------------------------------------------------------------

    def _scan_patch(self, diff: DiffFile) -> list[ReviewFinding]:
        findings: list[ReviewFinding] = []
        patch = diff.patch or ""
        lines = patch.splitlines()

        findings.extend(self._check_sql_injection(diff, lines))
        findings.extend(self._check_hardcoded_secrets(diff, lines))
        findings.extend(self._check_error_handling(diff, lines))
        findings.extend(self._check_large_functions(diff, lines))
        findings.extend(self._check_prompt_injection(diff, lines))
        findings.extend(self._check_open_security_group(diff, lines))
        findings.extend(self._check_missing_tests(diff, lines))

        return findings

    def _check_sql_injection(
        self, diff: DiffFile, lines: list[str]
    ) -> list[ReviewFinding]:
        return self._match_patterns(
            diff,
            lines,
            _SQL_INJECTION_PATTERNS,
            finding_category="sql-injection",
            title="Potential SQL injection",
            description=(
                "Raw string formatting detected in SQL query construction. "
                "Use parameterised queries to prevent injection."
            ),
            severity=RiskLevel.HIGH,
        )

    def _check_hardcoded_secrets(
        self, diff: DiffFile, lines: list[str]
    ) -> list[ReviewFinding]:
        return self._match_patterns(
            diff,
            lines,
            _HARDCODED_SECRET_PATTERNS,
            finding_category="hardcoded-secret",
            title="Hardcoded secret or credential",
            description=(
                "A potential secret or credential is hardcoded in the source. "
                "Move it to a secrets manager or environment variable."
            ),
            severity=RiskLevel.HIGH,
        )

    def _check_error_handling(
        self, diff: DiffFile, lines: list[str]
    ) -> list[ReviewFinding]:
        return self._match_patterns(
            diff,
            lines,
            _MISSING_ERROR_HANDLING_PATTERNS,
            finding_category="missing-error-handling",
            title="Missing error handling",
            description=(
                "A bare ``except: pass`` silently swallows exceptions. "
                "Handle or log the error explicitly."
            ),
            severity=RiskLevel.MEDIUM,
        )

    def _check_prompt_injection(
        self, diff: DiffFile, lines: list[str]
    ) -> list[ReviewFinding]:
        return self._match_patterns(
            diff,
            lines,
            _PROMPT_INJECTION_PATTERNS,
            finding_category="prompt-injection",
            title="Possible prompt injection attempt",
            description=(
                "Text resembling a prompt injection instruction was found. "
                "This may attempt to influence AI-based review output."
            ),
            severity=RiskLevel.HIGH,
        )

    def _check_open_security_group(
        self, diff: DiffFile, lines: list[str]
    ) -> list[ReviewFinding]:
        return self._match_patterns(
            diff,
            lines,
            _OPEN_SECURITY_GROUP_PATTERNS,
            finding_category="open-security-group",
            title="Security group open to the world",
            description=(
                "A security group or firewall rule allows traffic from "
                "0.0.0.0/0 — restrict to known CIDR blocks."
            ),
            severity=RiskLevel.HIGH,
        )

    def _check_large_functions(
        self, diff: DiffFile, lines: list[str]
    ) -> list[ReviewFinding]:
        findings: list[ReviewFinding] = []
        func_start: int | None = None
        func_name: str = ""

        for idx, line in enumerate(lines):
            if not line.startswith("+"):
                continue
            content = line[1:]
            match = re.match(r"^(\s*)def\s+(\w+)\s*\(", content)
            if match:
                # Close previous function if tracked
                if func_start is not None:
                    length = idx - func_start
                    if length > _LARGE_FUNCTION_LINE_THRESHOLD:
                        findings.append(
                            self._make_finding(
                                diff,
                                func_start,
                                idx,
                                "large-function",
                                f"Function `{func_name}` is {length} lines long",
                                (
                                    f"Function `{func_name}` exceeds "
                                    f"{_LARGE_FUNCTION_LINE_THRESHOLD} lines. "
                                    "Consider refactoring into smaller functions."
                                ),
                                RiskLevel.LOW,
                                content,
                            )
                        )
                func_start = idx
                func_name = match.group(2)

        # Check last tracked function
        if func_start is not None:
            length = len(lines) - func_start
            if length > _LARGE_FUNCTION_LINE_THRESHOLD:
                findings.append(
                    self._make_finding(
                        diff,
                        func_start,
                        len(lines) - 1,
                        "large-function",
                        f"Function `{func_name}` is {length} lines long",
                        (
                            f"Function `{func_name}` exceeds "
                            f"{_LARGE_FUNCTION_LINE_THRESHOLD} lines. "
                            "Consider refactoring into smaller functions."
                        ),
                        RiskLevel.LOW,
                        lines[func_start] if func_start < len(lines) else "",
                    )
                )
        return findings

    def _check_missing_tests(
        self, diff: DiffFile, lines: list[str]
    ) -> list[ReviewFinding]:
        """Flag source files that have no corresponding test file in the diff."""
        findings: list[ReviewFinding] = []
        path = diff.path
        if (
            path.endswith(".py")
            and not path.startswith("test")
            and "test_" not in path
            and "/tests/" not in path
        ):
            has_function = any(
                re.match(r"^\+\s*def\s+\w+", ln) for ln in lines
            )
            if has_function:
                findings.append(
                    self._make_finding(
                        diff,
                        0,
                        None,
                        "missing-tests",
                        "No test coverage for new/modified functions",
                        (
                            f"File `{path}` adds or modifies functions but no "
                            "corresponding test file is included in this PR."
                        ),
                        RiskLevel.MEDIUM,
                        "",
                    )
                )
        return findings

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _match_patterns(
        self,
        diff: DiffFile,
        lines: list[str],
        patterns: list[re.Pattern[str]],
        *,
        finding_category: str,
        title: str,
        description: str,
        severity: RiskLevel,
    ) -> list[ReviewFinding]:
        findings: list[ReviewFinding] = []
        for idx, line in enumerate(lines):
            if not line.startswith("+"):
                continue
            content = line[1:]
            for pat in patterns:
                if pat.search(content):
                    findings.append(
                        self._make_finding(
                            diff,
                            idx,
                            idx,
                            finding_category,
                            title,
                            description,
                            severity,
                            content,
                        )
                    )
                    break  # one finding per line
        return findings

    @staticmethod
    def _make_finding(
        diff: DiffFile,
        line_start: int,
        line_end: int | None,
        category: str,
        title: str,
        description: str,
        severity: RiskLevel,
        evidence: str,
    ) -> ReviewFinding:
        return ReviewFinding(
            finding_id=f"offline-{uuid.uuid4().hex[:8]}",
            severity=severity,
            category=category,
            file_path=diff.path,
            line_start=line_start,
            line_end=line_end,
            title=title,
            description=description,
            evidence=evidence.strip(),
            suggestion="",
            confidence=0.85,
            reviewer_id="offline-reviewer",
        )

    @staticmethod
    def _build_summary(findings: list[ReviewFinding]) -> str:
        if not findings:
            return "No issues detected by offline pattern analysis."
        counts: dict[str, int] = {}
        for f in findings:
            counts[f.category] = counts.get(f.category, 0) + 1
        parts = [f"{cat}: {n}" for cat, n in sorted(counts.items())]
        return f"Found {len(findings)} issue(s): " + ", ".join(parts)
