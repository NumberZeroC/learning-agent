#!/bin/bash
# Setup script for Claude Code Python

set -e

echo "🚀 Setting up Claude Code Python..."
echo

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "❌ uv not found. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "✓ uv found"

# Install Python 3.11
echo "📦 Installing Python 3.11..."
uv python install 3.11

# Create virtual environment
echo "🌐 Creating virtual environment..."
uv venv --python 3.11

# Activate and install dependencies
echo "📥 Installing dependencies..."
source .venv/bin/activate
uv pip install -e ".[dev]"

echo
echo "✅ Setup complete!"
echo
echo "To activate the environment:"
echo "  source .venv/bin/activate"
echo
echo "To run the CLI:"
echo "  ccp --help"
echo
echo "To run tests:"
echo "  pytest"
