#!/usr/bin/env bash
set -euo pipefail

echo "=================================================="
echo "Jenkins Agentic PR Review — Offline Demonstration"
echo "=================================================="

export PYTHONPATH="src:."
python -m pr_review.cli demo --artifacts-dir artifacts
