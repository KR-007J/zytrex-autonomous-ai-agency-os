#!/usr/bin/env bash
# ==============================================================================
# Enterprise Lead Generation & LinkedIn Outreach Agent Installer
# ==============================================================================
set -e

echo "======================================================================"
echo "🚀 Installing LeadGen & LinkedIn Outreach Agent (Hermes Runtime)..."
echo "======================================================================"

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is required but not installed."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✓ Found Python $PYTHON_VERSION"

# Ensure uv is installed
if ! command -v uv &> /dev/null && [ ! -f "$HOME/.local/bin/uv" ]; then
    echo "📦 Installing uv fast package installer..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
else
    export PATH="$HOME/.local/bin:$PATH"
    echo "✓ Found uv package manager"
fi

# Create virtual environment
echo "🐍 Creating virtual environment in .venv..."
uv venv .venv
VENV_PY="./.venv/bin/python"

# Install project dependencies
echo "📦 Installing required dependencies..."
uv pip install -e . --python "$VENV_PY"

# Ensure database and data directory exist
mkdir -p data

# Initialize database schema
echo "🗄️ Initializing SQLite database schema..."
"$VENV_PY" -c "from src.database.db import init_db; init_db()"

# Register with Hermes Agent if installed
if [ -d "$HOME/.hermes/skills" ]; then
    echo "🤖 Registering leadgen-skill with Hermes Agent..."
    mkdir -p "$HOME/.hermes/skills/productivity"
    rm -rf "$HOME/.hermes/skills/productivity/leadgen-skill"
    cp -r ./leadgen-skill "$HOME/.hermes/skills/productivity/leadgen-skill"
    echo "✓ leadgen-skill installed to $HOME/.hermes/skills/productivity/leadgen-skill"
fi

echo "======================================================================"
echo "🎉 Installation complete!"
echo ""
echo "Quick Start Commands:"
echo "  1. Start Web Dashboard:  ./.venv/bin/python leadgen-skill/scripts/run_leadgen.py --mode serve"
echo "  2. Run Search Scraper:   ./.venv/bin/python leadgen-skill/scripts/run_leadgen.py --mode scrape"
echo "  3. Generate Outreach:    ./.venv/bin/python leadgen-skill/scripts/run_leadgen.py --mode outreach"
echo "  4. Run Pytest Suite:     ./.venv/bin/pytest tests/ -v"
echo "======================================================================"
