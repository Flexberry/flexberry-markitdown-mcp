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

# Check if installing from PyPI or local
if [ -f "pyproject.toml" ]; then
    echo "Installing from local source..."
    
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
else
    echo "Installing from PyPI..."
    pip install --upgrade pip
    pip install flexberry-markitdown-mcp
fi

echo ""
echo "=== Installation complete! ==="
echo ""
echo "To configure RooCode, add this to your mcp_settings.json:"
echo ""
echo '{'
echo '  "mcpServers": {'
echo '    "flexberry-markitdown": {'
echo '      "command": "python3",'
echo '      "args": ["-m", "flexberry_markitdown_mcp.server"]'
echo '    }'
echo '  }'
echo '}'
echo ""
echo "Repository: https://github.com/Flexberry/flexberry-markitdown-mcp"
echo ""
