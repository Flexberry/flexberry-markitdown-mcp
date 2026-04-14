#!/bin/bash
# Uninstallation script for Linux/macOS

set -e

echo "=== Flexberry MarkItDown MCP Server Uninstallation ==="

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Nothing to uninstall."
    exit 0
fi

# Ask for confirmation
read -p "Remove virtual environment? (y/N): " CONFIRM
if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "Cancelled."
    exit 0
fi

echo "Removing virtual environment..."
rm -rf .venv

echo ""
echo "Virtual environment removed."
echo ""
echo "To complete uninstallation:"
echo "1. Remove the MCP configuration from RooCode settings"
echo "2. Delete this folder: $(pwd)"
echo "3. Optionally delete logs: ~/.flexberry-markitdown-mcp"
echo ""
