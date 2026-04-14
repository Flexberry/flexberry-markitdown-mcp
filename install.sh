#!/bin/bash
# Installation script for Linux/macOS

set -e

echo "=== Flexberry MarkItDown MCP Server Installation ==="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python: $PYTHON_VERSION"

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -e .

echo ""
echo "=== Installation complete! ==="
echo ""
echo "To configure RooCode, add this to your mcp_settings.json:"
echo ""
echo '{'
echo '  "mcpServers": {'
echo '    "flexberry-markitdown": {'
echo '      "command": "'$(pwd)'/.venv/bin/python",'
echo '      "args": ["-m", "flexberry_markitdown_mcp.server"],'
echo '      "cwd": "'$(pwd)'"'
echo '    }'
echo '  }'
echo '}'
echo ""
echo "Repository: https://github.com/Flexberry/flexberry-markitdown-mcp"
echo ""
