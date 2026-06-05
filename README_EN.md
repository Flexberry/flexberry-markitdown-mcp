# Flexberry MarkItDown MCP Server

MCP server for bidirectional document conversion:
- **Any format → Markdown** (via Microsoft MarkItDown)
- **Markdown → PDF** (via Playwright / headless Chromium — same as vscode-markdown-pdf)

Based on:
- [flexberry-markitdown-mcp](https://github.com/Flexberry/flexberry-markitdown-mcp) — PDF → MD
- [vscode-markdown-pdf](https://github.com/showzs/vscode-markdown-pdf) — MD → PDF concept

## Installation — one command

```bash
pip install flexberry-markitdown-mcp
```

That's it! On first `convert_to_pdf` call, Chromium is auto-downloaded (same as vscode-markdown-pdf).

### Optional extras

```bash
# Lightweight backend without browser (no JS rendering)
pip install flexberry-markitdown-mcp[weasyprint]

# For development
pip install flexberry-markitdown-mcp[dev]
```

## Features

### Convert to Markdown (`convert_to_markdown`)
- 30+ formats: PDF, DOCX, PPTX, XLSX, HTML, images (OCR), audio (transcription), EPUB, ZIP...
- Cyrillic filename and content support
- Atomic writes (temp file + rename)

### Convert to PDF (`convert_to_pdf`)
- **Playwright** (default) — headless Chromium, same as vscode-markdown-pdf
  - Chromium auto-downloaded on first use
  - Supports JavaScript-rendered content (Mermaid, PlantUML, etc.)
  - Headers/footers with page numbers
- **WeasyPrint** (optional) — pure Python, no browser required
- GitHub-flavored styling (tables, code, blockquotes)
- Syntax highlighting via Pygments
- Configurable page format, margins, custom CSS

## MCP Client Configuration

### Claude Desktop / RooCode / Cursor

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

### Via uv

```json
{
  "mcpServers": {
    "flexberry-markitdown": {
      "command": "uv",
      "args": [
        "--directory", "/path/to/flexberry-markitdown-mcp-with-pdf",
        "run", "flexberry-markitdown-mcp"
      ]
    }
  }
}
```

## Tools

### `convert_to_markdown`
Converts a file of any supported format to Markdown.

| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `file_path` | string | ✅ | Absolute path to the file |
| `output_path` | string | ❌ | Custom output path |
| `overwrite` | boolean | ❌ | Overwrite existing (default: false) |

### `convert_to_pdf`
Converts a Markdown file to PDF. Default backend: **Playwright** (same as vscode-markdown-pdf).

| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `file_path` | string | ✅ | Absolute path to the .md file |
| `output_path` | string | ❌ | Custom PDF output path |
| `backend` | string | ❌ | `"playwright"` (default) or `"weasyprint"` |
| `overwrite` | boolean | ❌ | Overwrite existing (default: false) |
| `custom_css` | string | ❌ | Additional CSS |
| `include_default_styles` | boolean | ❌ | Include built-in styles (default: true) |
| `format` | string | ❌ | Paper format: A4, Letter, etc. (default: A4) |
| `margin_top` | string | ❌ | Top margin (default: 1.5cm) |
| `margin_bottom` | string | ❌ | Bottom margin (default: 1cm) |
| `margin_left` | string | ❌ | Left margin (default: 1cm) |
| `margin_right` | string | ❌ | Right margin (default: 1cm) |
| `print_background` | boolean | ❌ | Print background (default: true) |
| `display_header_footer` | boolean | ❌ | Header/footer (default: true, Playwright) |

### `get_supported_formats`
Returns supported formats and available PDF backends.

### `check_file_exists`
Checks if a file exists and returns its info.

### `list_directory`
Lists directory contents.

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                   MCP Server (stdio)                  │
├──────────────────────────────────────────────────────┤
│                                                       │
│  convert_to_markdown          convert_to_pdf          │
│  ┌───────────────┐            ┌──────────────────┐   │
│  │  MarkItDown   │            │  markdown-it-py  │   │
│  │  (any→MD)     │            │  (MD→HTML)       │   │
│  └───────┬───────┘            └────────┬─────────┘   │
│          │                             │              │
│          ▼                             ▼              │
│  ┌───────────────┐            ┌──────────────────┐   │
│  │  Atomic write │            │  HTML template   │   │
│  │  (MD to disk) │            │  + GitHub CSS    │   │
│  └───────────────┘            └────────┬─────────┘   │
│                                        │              │
│                              ┌─────────┴──────────┐  │
│                              ▼                    ▼  │
│                     ┌──────────────┐  ┌────────────┐ │
│                     │  Playwright  │  │ WeasyPrint │ │
│                     │  (DEFAULT)   │  │ (optional) │ │
│                     │  Chromium    │  │ Pure Python│ │
│                     │  auto-d/l    │  │ No JS      │ │
│                     └──────┬───────┘  └─────┬──────┘ │
│                            ▼                ▼        │
│                     ┌─────────────────────────────┐  │
│                     │      PDF saved to disk      │  │
│                     └─────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

## PDF Backend Comparison

| Feature | Playwright (default) | WeasyPrint (optional) |
|---|---|---|
| Install | Auto with `pip install` | `pip install ...[weasyprint]` |
| Chromium | Auto-download on first use | Not needed |
| JavaScript | ✅ Full support | ❌ |
| Mermaid/PlantUML | ✅ | ❌ |
| Headers/footers | ✅ Page numbers | Via CSS @page |
| Recommendation | All documents | Lightweight fallback |

## License

MIT
