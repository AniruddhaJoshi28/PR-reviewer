$ErrorActionPreference = "Stop"

Write-Host ">>> Running test suite..." -ForegroundColor Cyan
$env:PYTHONPATH = "src;."
pytest tests/ -v

Write-Host ">>> Running evaluation benchmarks..." -ForegroundColor Cyan
python -m pr_review.cli evaluate

Write-Host ">>> Running offline vertical slice demo..." -ForegroundColor Cyan
python -m pr_review.cli demo

Write-Host ">>> All validations passed successfully!" -ForegroundColor Green
