"""Security tests: Verifies that credentials and tokens never appear in logs or reports."""

from pathlib import Path
from pr_review.models.base import DiffFile, PRMetadata, RiskLevel, SCMProviderType
from pr_review.orchestration.pipeline import ReviewPipeline
from pr_review.scm.discovery import sanitize_url


def test_sanitize_url_scrubs_passwords():
    assert sanitize_url("https://user:SuperSecretPassword123@gitlab.enterprise.com/repo.git") == "https://***:***@gitlab.enterprise.com/repo.git"


def test_no_raw_secrets_in_generated_reports(tmp_path: Path):
    pipeline = ReviewPipeline(artifacts_dir=str(tmp_path), offline_demo=True, ai_provider="offline")
    report = pipeline.run_offline_demo()

    # Search for known secret in reports
    secret = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

    rev_json = (tmp_path / "review.json").read_text(encoding="utf-8")
    rev_md = (tmp_path / "review.md").read_text(encoding="utf-8")
    sarif = (tmp_path / "review.sarif").read_text(encoding="utf-8")

    assert secret not in rev_json
    assert secret not in rev_md
    assert secret not in sarif
