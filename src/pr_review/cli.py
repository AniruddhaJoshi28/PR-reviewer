"""Command line interface for the PR Review and Evaluation Platform."""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from pr_review.models.base import DiffFile, RiskLevel
from pr_review.orchestration.pipeline import ReviewPipeline
from pr_review.risk.classifier import RiskClassifier
from pr_review.scanners.aggregate import ScannerOrchestrator

app = typer.Typer(
    name="pr-review",
    help="Jenkins-Native Agentic PR Review & Security Platform",
    add_completion=False,
)
console = Console()


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


@app.command()
def demo(
    artifacts_dir: str = typer.Option("artifacts", "--artifacts-dir", "-a", help="Output directory for reports"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
) -> None:
    """Run an end-to-end offline demonstration of the PR review pipeline without external credentials."""
    setup_logging(verbose)
    console.print(Panel.fit("[bold cyan]Jenkins Agentic PR Review — Offline Demonstration[/bold cyan]"))

    pipeline = ReviewPipeline(artifacts_dir=artifacts_dir, offline_demo=True, ai_provider="offline")
    report = pipeline.run_offline_demo()

    # Display Summary Table
    table = Table(title="Review Pipeline Execution Summary")
    table.add_column("Stage / Item", style="bold white")
    table.add_column("Result / Details", style="cyan")

    table.add_row("PR Identifier", f"#{report.pr_metadata.pr_id} ({report.pr_metadata.title})")
    table.add_row("Commit SHA", report.pr_metadata.head_sha[:12])
    table.add_row("SCM Provider", report.pr_metadata.provider.value)
    table.add_row("Risk Level", f"[bold red]{report.risk_classification.risk_level.value}[/bold red]")
    table.add_row("Triggered Rules", ", ".join(report.risk_classification.rule_ids))

    scanner_summary = ", ".join(f"{s.scanner_name}: {s.status.value}" for s in report.scan_results)
    table.add_row("Security Scanners", scanner_summary)

    agent_count = len(report.agent_reviews)
    table.add_row("Agent Reviews", f"{agent_count} reviews, {len(report.debate_rounds)} debate rounds")

    policy_decision = report.policy_result.decision.value if report.policy_result else "UNKNOWN"
    table.add_row("Policy Decision", f"[bold yellow]{policy_decision}[/bold yellow]")
    table.add_row("Artifacts Generated", f"{artifacts_dir}/ (review.json, review.md, review.sarif, tests.xml, policy-decision.json)")

    console.print(table)
    console.print(f"\n[green]✔ Offline demo completed successfully! Artifacts written to {artifacts_dir}/[/green]")


@app.command()
def review(
    artifacts_dir: str = typer.Option("artifacts", "--artifacts-dir", "-a", help="Output directory for reports"),
    offline: bool = typer.Option(False, "--offline", help="Run in offline mock mode without real scanners"),
    ai_provider: str = typer.Option("offline", "--ai-provider", help="AI provider (offline, codex, claude)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
) -> None:
    """Run full PR review pipeline in CI/Jenkins environment."""
    setup_logging(verbose)
    pipeline = ReviewPipeline(artifacts_dir=artifacts_dir, offline_demo=offline, ai_provider=ai_provider)
    report = pipeline.run_pipeline()

    policy = report.policy_result
    if policy and policy.decision.value == "BLOCKED":
        console.print(f"[bold red]Pipeline BLOCKED by policy: {', '.join(policy.reasons)}[/bold red]")
        sys.exit(1)
    elif policy and policy.decision.value == "HUMAN_APPROVAL_REQUIRED":
        console.print(f"[bold yellow]HUMAN APPROVAL REQUIRED: {', '.join(policy.reasons)}[/bold yellow]")
        sys.exit(0)
    else:
        console.print("[bold green]Pipeline PASSED all gates.[/bold green]")
        sys.exit(0)


@app.command()
def risk(
    diff_file: Optional[Path] = typer.Option(None, "--file", "-f", help="Optional path to patch file to analyze"),
) -> None:
    """Run deterministic risk classification on local changeset or file."""
    classifier = RiskClassifier()
    if diff_file and diff_file.exists():
        patch_text = diff_file.read_text(encoding="utf-8")
        diffs = [DiffFile(path=diff_file.name, status="M", patch=patch_text)]
    else:
        diffs = [
            DiffFile(path="src/auth.py", status="M", patch="+password = 'admin123'\n"),
        ]
    res = classifier.classify(diffs)
    console.print(json.dumps(res.model_dump(mode="json"), indent=2))


@app.command()
def scan(
    offline: bool = typer.Option(True, "--offline/--real", help="Run in mock/offline mode"),
) -> None:
    """Run security scanners on the local workspace."""
    orchestrator = ScannerOrchestrator(offline_demo=offline)
    diffs = [DiffFile(path="src/api.py", status="M", patch="+query = f'SELECT * FROM users WHERE x={x}'\n")]
    results = orchestrator.scan_all(diffs)
    for r in results:
        console.print(f"[{r.scanner_name}] Status: {r.status.value} (Passed={r.passed}, Mock={r.is_mock})")


@app.command()
def evaluate(
    fixtures_dir: str = typer.Option("evaluations/fixtures", "--fixtures-dir", help="Path to evaluation fixtures"),
    labels_file: str = typer.Option("evaluations/ground_truth/labels.json", "--labels", help="Path to ground truth labels"),
    artifacts_dir: str = typer.Option("artifacts", "--artifacts-dir", "-a", help="Output directory for reports"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
) -> None:
    """Run full evaluation benchmark suite across 4 architectures using ground-truth fixtures."""
    setup_logging(verbose)
    console.print(Panel.fit("[bold magenta]AI PR Review Evaluation Benchmark Suite[/bold magenta]"))
    
    from evaluations.runner import EvaluationRunner
    runner = EvaluationRunner(fixtures_dir=fixtures_dir, labels_path=labels_file, artifacts_dir=artifacts_dir)
    summary = runner.run_benchmark()

    # Display benchmark comparison table
    table = Table(title="Architecture Evaluation Comparison")
    table.add_column("Metric", style="bold white")
    table.add_column("Deterministic", style="cyan")
    table.add_column("Single-Agent", style="blue")
    table.add_column("Multi-Agent", style="magenta")
    table.add_column("Combined", style="green")

    metrics = summary["metrics"]
    m_det = metrics["Deterministic-Only"]
    m_sa = metrics["Single-Agent"]
    m_ma = metrics["Multi-Agent"]
    m_comb = metrics["Combined"]

    table.add_row("Precision", f"{m_det['precision']:.1%}", f"{m_sa['precision']:.1%}", f"{m_ma['precision']:.1%}", f"{m_comb['precision']:.1%}")
    table.add_row("Recall", f"{m_det['recall']:.1%}", f"{m_sa['recall']:.1%}", f"{m_ma['recall']:.1%}", f"{m_comb['recall']:.1%}")
    table.add_row("F1 Score", f"{m_det['f1']:.3f}", f"{m_sa['f1']:.3f}", f"{m_ma['f1']:.3f}", f"{m_comb['f1']:.3f}")
    table.add_row("High-Risk FN", str(m_det['high_risk_false_negatives']), str(m_sa['high_risk_false_negatives']), str(m_ma['high_risk_false_negatives']), str(m_comb['high_risk_false_negatives']))
    table.add_row("Mean Latency", f"{m_det['mean_latency_seconds']:.3f}s", f"{m_sa['mean_latency_seconds']:.3f}s", f"{m_ma['mean_latency_seconds']:.3f}s", f"{m_comb['mean_latency_seconds']:.3f}s")
    table.add_row("Tokens Used", str(m_det['total_tokens']), str(m_sa['total_tokens']), str(m_ma['total_tokens']), str(m_comb['total_tokens']))

    console.print(table)
    console.print(f"\n[green]✔ Evaluation complete! Reports generated in {artifacts_dir}/ (evaluation.json, evaluation.md, evaluation.xml)[/green]")


@app.command()
def version() -> None:
    """Display platform version."""
    console.print("jenkins-agentic-pr-review v1.0.0")


if __name__ == "__main__":
    app()
