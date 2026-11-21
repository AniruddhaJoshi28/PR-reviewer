"""Security tests: Verifies that malicious branch names or PR titles cannot execute arbitrary commands."""

import pytest
from pr_review.models.base import DiffFile, PRMetadata, SCMProviderType
from pr_review.orchestration.pipeline import ReviewPipeline


def test_malicious_branch_name_cannot_inject_shell(tmp_path):
    pipeline = ReviewPipeline(artifacts_dir=str(tmp_path), offline_demo=True)
    meta = PRMetadata(
        pr_id="101; rm -rf /",
        title="Malicious PR $(reboot)",
        description="`touch /tmp/pwned`",
        source_branch="feat; echo injection",
        target_branch="main && echo pwn",
        base_sha="1111111111111111111111111111111111111111",
        head_sha="2222222222222222222222222222222222222222",
        author="hacker",
        provider=SCMProviderType.GENERIC_GIT,
    )
    diff = [DiffFile(path="code.py", status="M", patch="+x = 1\n")]

    # Should run cleanly without shell syntax execution or unhandled subprocess error
    report = pipeline.run_pipeline(custom_diff=diff, custom_metadata=meta)
    assert report.pr_metadata.pr_id == "101; rm -rf /"
    assert (tmp_path / "review.json").exists()
