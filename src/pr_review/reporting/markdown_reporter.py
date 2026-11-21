"""Markdown executive summary report generator."""

from __future__ import annotations

from pathlib import Path
from pr_review.models.base import ReviewReport, RiskLevel, PolicyDecision


class MarkdownReporter:
    """Generates human-readable Markdown review summaries."""

    @staticmethod
    def generate_review_md(report: ReviewReport, output_path: str | Path) -> str:
        pr = report.pr_metadata
        risk = report.risk_classification
        policy = report.policy_result
        decision_str = policy.decision.value if policy else "UNKNOWN"

        badge_colors = {
            "PASS": "🟢",
            "BLOCKED": "🔴",
            "HUMAN_APPROVAL_REQUIRED": "🟡",
            "INCOMPLETE": "⚪",
        }
        badge = badge_colors.get(decision_str, "⚪")

        md = []
        md.append(f"# Automated PR Review Summary {badge} `{decision_str}`\n")
        md.append(f"**PR**: #{pr.pr_id} — *{pr.title}*  ")
        md.append(f"**Author**: `{pr.author}` | **Branches**: `{pr.source_branch}` ➔ `{pr.target_branch}`  ")
        md.append(f"**Commit SHA**: `{pr.head_sha[:12]}` | **SCM Provider**: `{pr.provider.value}`  \n")

        md.append("---")
        md.append("## 1. Deterministic Risk Classification")
        md.append(f"- **Risk Level**: **`{risk.risk_level.value}`**")
        md.append(f"- **Reasoning**: {risk.reasoning_summary}")
        if risk.rule_ids:
            md.append(f"- **Triggered Rules**: `{'`, `'.join(risk.rule_ids)}`")
        if risk.evidence:
            md.append("\n**Risk Evidence:**")
            for ev in risk.evidence[:5]:
                md.append(f"- {ev}")

        md.append("\n---")
        md.append("## 2. Security Scanners Execution")
        md.append("| Scanner | Status | Passed | Mock Mode | Findings | Notes |")
        md.append("| :--- | :---: | :---: | :---: | :---: | :--- |")
        for s in report.scan_results:
            is_mock_str = "Yes (Demo)" if s.is_mock else "No (Real)"
            notes = s.error_message or "-"
            md.append(f"| **{s.scanner_name}** | `{s.status.value}` | {'✅' if s.passed else '❌'} | {is_mock_str} | {len(s.findings)} | {notes} |")

        md.append("\n---")
        md.append("## 3. Agent Reviews & Debate Verdict")
        if report.agent_reviews:
            for rev in report.agent_reviews:
                md.append(f"### Role: `{rev.agent_role}` ({rev.agent_id})")
                md.append(f"{rev.summary}")
                if rev.findings:
                    md.append("\n**Findings:**")
                    for f in rev.findings:
                        md.append(f"- **[{f.severity.value}]** `{f.file_path}`: {f.title}")
                        md.append(f"  - *Description*: {f.description}")
                        if f.evidence:
                            md.append(f"  - *Evidence*: `{f.evidence}`")
                        if f.suggestion:
                            md.append(f"  - *Suggestion*: {f.suggestion}")
        else:
            md.append("*No agent reviews recorded.*")

        if report.debate_rounds:
            md.append("\n### Adversarial Debate Outcome")
            for dr in report.debate_rounds:
                md.append(f"- **Round {dr.round_number}**: {dr.judge_decision}")
                for ch in dr.challenges:
                    md.append(f"  - *Challenge by {ch.challenger_id}*: {ch.reason} (Action: `{ch.suggested_action}`)")

        md.append("\n---")
        md.append("## 4. Policy Gate & Merge Eligibility")
        if policy:
            md.append(f"- **Decision**: **`{policy.decision.value}`**")
            md.append(f"- **Mandatory Checks Passed**: {'Yes' if policy.mandatory_checks_passed else 'No'}")
            if policy.human_approvers:
                md.append(f"- **Required Approvers**: `{'`, `'.join(policy.human_approvers)}`")
            if policy.reasons:
                md.append("\n**Policy Reasons:**")
                for r in policy.reasons:
                    md.append(f"- {r}")

        md.append("\n> **IMPORTANT ENTERPRISE NOTICE:**  ")
        md.append("> *Jenkins policy decisions reflect CI analysis only. Git provider branch protection must be explicitly configured to enforce required merge gates on the remote repository.*")

        content = "\n".join(md) + "\n"
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(content, encoding="utf-8")
        return content
