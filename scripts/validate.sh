#!/usr/bin/env bash
set -euo pipefail

echo ">>> Running test suite..."
export PYTHONPATH="src:."
pytest tests/ -v

echo ">>> Running evaluation benchmarks..."
python -m pr_review.cli evaluate

echo ">>> Running offline vertical slice demo..."
python -m pr_review.cli demo

echo ">>> All validations passed successfully!"
