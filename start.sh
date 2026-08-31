#!/usr/bin/env bash
# ==============================================================================
# Autonomous AI Agency — 1-Click Turnkey Startup Script
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================================================"
echo " ⚡ STARTING AUTONOMOUS AI AGENCY OPERATING SYSTEM (TURNKEY READY)"
echo "================================================================================"

# Create virtualenv if not exists
if [ ! -d ".venv" ]; then
    echo "📦 Initializing local virtual environment..."
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -e .
fi

# Launch application with automatic browser opening
echo "🚀 Launching Mission Control..."
.venv/bin/python launcher.py
