$ErrorActionPreference = "Stop"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Jenkins Agentic PR Review — Offline Demonstration" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

$env:PYTHONPATH = "src;."
python -m pr_review.cli demo --artifacts-dir artifacts
