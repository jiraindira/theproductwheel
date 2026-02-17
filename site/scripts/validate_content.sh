#!/usr/bin/env bash
set -euo pipefail

ARGS="${*:-}"

# Run from site/, validation lives at repo root
cd ..

# Prefer python3, fallback to python
PY=python3
command -v python3 >/dev/null 2>&1 || PY=python

# Create an isolated venv inside the repo (allowed on Vercel)
$PY -m venv .venv_validate

# Activate it
# shellcheck disable=SC1091
source .venv_validate/bin/activate

# Upgrade pip inside venv and install minimal deps
python -m pip install --upgrade pip
python -m pip install -r requirements-vercel.txt

# Run validation
python validate_content.py $ARGS
