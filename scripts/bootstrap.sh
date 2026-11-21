#!/usr/bin/env bash
set -euo pipefail

echo "Setting up Python virtual environment..."
python -m venv .venv
source .venv/bin/activate || source .venv/Scripts/activate

echo "Installing project and dependencies..."
pip install --upgrade pip
pip install -e ".[dev]"

echo "Bootstrap complete! Activate your venv and run scripts/validate.sh"
