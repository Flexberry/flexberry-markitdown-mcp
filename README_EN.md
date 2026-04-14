# Flexberry MarkItDown MCP Server

[![GitHub](https://img.shields.io/badge/GitHub-Flexberry%2Fflexberry--markitdown--mcp-blue)](https://github.com/Flexberry/flexberry-markitdown-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://img.shields.io/pypi/v/flexberry-markitdown-mcp)](https://pypi.org/project/flexberry-markitdown-mcp/)

MCP server for converting files to Markdown using MarkItDown library by Microsoft.

## Features

- 🔄 **File conversion** of various formats to Markdown
- 📁 **Large files** - result is saved to disk, not loaded into LLM context
- 🌍 **Cyrillic support** in documents and filenames
- 💻 **Cross-platform** - Windows and Linux
- 🔧 **Integration with RooCode** via Model Context Protocol

## Supported Formats

| Category | Formats |
|----------|---------|
| Documents | PDF, DOCX, DOC, PPTX, PPT, XLSX, XLS |
| Web | HTML, HTM, XML, URL |
| Data | CSV, JSON |
| Text | MD, RST, TXT |
| Images (OCR) | PNG, JPG, JPEG, GIF, BMP, TIFF, WEBP |
| Audio (transcription) | MP3, WAV, M4A, OGG, FLAC |
| Archives | ZIP |
| E-books | EPUB |

> ⚠️ For OCR images, Tesseract is required. For audio transcription, system support is needed.

## Installation

### Option 1: Install from PyPI (recommended)

```bash
# Install via pip
pip install flexberry-markitdown-mcp

# Install with development dependencies
pip install flexberry-markitdown-mcp[dev]
```

### Option 2: Install from source

```bash
# Clone the repository
git clone https://github.com/Flexberry/flexberry-markitdown-mcp.git
cd flexberry-markitdown-mcp

# Create virtual environment (optional but recommended)
python -m venv .venv

# Activate virtual environment
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# Install dependencies
pip install -e .
```

### Option 3: Use installation scripts

#### Linux/macOS:
```bash
chmod +x install.sh
./install.sh
```

#### Windows:
```cmd
install.bat
```

## RooCode Configuration

### Windows Configuration

Add to RooCode settings (`mcp_settings.json` or via interface):

```json
{
  "mcpServers": {
    "flexberry-markitdown": {
      "command": "python",
      "args": ["-m", "flexberry_markitdown_mcp.server"]
    }
  }
}
```

Or with virtual environment:

```json
{
  "mcpServers": {
    "flexberry-markitdown": {
      "command": "C:\\path\\to\\flexberry-markitdown-mcp\\.venv\\Scripts\\python.exe",
      "args": ["-m", "flexberry_markitdown_mcp.server"],
      "cwd": "C:\\path\\to\\flexberry-markitdown-mcp"
    }
  }
}
```

### Linux Configuration

```json
{
  "mcpServers": {
    "flexberry-markitdown": {
      "command": "python3",
      "args": ["-m", "flexberry_markitdown_mcp.server"]
    }
  }
}
```

Or with virtual environment:

```json
{
  "mcpServers": {
    "flexberry-markitdown": {
      "command": "/home/user/flexberry-markitdown-mcp/.venv/bin/python",
      "args": ["-m", "flexberry_markitdown_mcp.server"],
      "cwd": "/home/user/flexberry-markitdown-mcp"
    }
  }
}
```

### Universal Configuration (via uv)

If using [uv](https://github.com/astral-sh/uv):

```json
{
  "mcpServers": {
    "flexberry-markitdown": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/flexberry-markitdown-mcp",
        "run",
        "flexberry-markitdown-mcp"
      ]
    }
  }
}
```

## Available Tools

### `convert_to_markdown`

Converts a file to Markdown and saves the result next to the original file.

**Parameters:**
- `file_path` (required) - path to the file for conversion
- `output_path` (optional) - custom path for saving the result
- `overwrite` (optional, default `false`) - overwrite existing file

**Example usage in RooCode:**
```
Convert file /home/user/documents/report.pdf to Markdown
```

### `get_supported_formats`

Returns a list of supported file formats.

### `check_file_exists`

Checks if a file exists and returns information about it.

## Usage Examples

### Converting PDF with Cyrillic

```
Convert file C:\Documents\Report 2024.pdf to Markdown
```

Result will be saved to `C:\Documents\Report 2024.md`

### Converting with overwrite

```
Convert file /home/user/report.docx with overwrite existing
```

### Converting to specified location

```
Convert presentation.pptx and save result to /tmp/output.md
```

## Large File Handling

The server is designed to work with files of any size:

1. File is converted via MarkItDown
2. Result is saved to disk next to the original file
3. Only information about path and size is returned to LLM context

This allows working with files that are 100x larger than LLM context limit.

## Logging

Server logs are saved to:
- Linux: `~/.flexberry-markitdown-mcp/server.log`
- Windows: `C:\Users\<user>\.flexberry-markitdown-mcp\server.log`

## Troubleshooting

### Error: "MarkItDown not installed"

```bash
pip install flexberry-markitdown-mcp
```

### Error: "MCP module not found"

```bash
pip install flexberry-markitdown-mcp
```

### Cyrillic issues in Windows

Ensure UTF-8 encoding in terminal. Server automatically sets UTF-8 for stdin/stdout/stderr.

### OCR not working for images

Install Tesseract:
- Windows: download from https://github.com/UB-Mannheim/tesseract/wiki
- Linux: `sudo apt install tesseract-ocr` (Ubuntu/Debian)

For Russian language, install language pack:
- Windows: select Russian language during installation
- Linux: `sudo apt install tesseract-ocr-rus`

### Audio transcription not working

MarkItDown uses Azure Speech Services for transcription. Ensure environment variables are configured.

## Development

### Running tests

```bash
pip install -e ".[dev]"
pytest
```

### Project structure

```
flexberry-markitdown-mcp/
├── src/
│   └── flexberry_markitdown_mcp/
│       ├── __init__.py
│       └── server.py
├── pyproject.toml
├── README_EN.md
├── install.sh
├── install.bat
├── uninstall.sh
├── uninstall.bat
└── roocode-config-examples.json
```

## License

MIT License

---

Developed by [Flexberry](https://github.com/Flexberry) team.
