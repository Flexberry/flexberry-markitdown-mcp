# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Flexberry MarkItDown MCP Server — MCP-сервер для двунаправленной конвертации документов: любой формат → Markdown (через Microsoft MarkItDown) и Markdown → PDF (через Playwright/WeasyPrint). Транспорт — stdio. Python 3.10+.

## Commands

```bash
# Install in development mode (all test/lint deps)
pip install -e ".[dev]"

# Install with both PDF backends
pip install -e ".[weasyprint]"
playwright install chromium

# Run all tests
pytest

# Run a single test file / class / function
pytest tests/test_converter.py
pytest tests/test_converter.py::TestMarkdownToHtml::test_table
pytest tests/test_server.py::TestServerTools::test_call_tool_convert_to_pdf_basic

# Lint
ruff check src/
ruff format --check src/

# Auto-fix lint and format
ruff check --fix src/
ruff format src/

# Run server locally (for MCP client testing)
python -m flexberry_markitdown_mcp.server
```

## Architecture

### Pipeline: Any → Markdown → PDF

The server exposes 5 MCP tools. Two core conversion pipelines:

**convert_to_markdown** — delegates entirely to `MarkItDown.convert()`. Result is saved to disk via atomic write (temp file + rename). Handles Unicode/Cyrillic filenames through NFC/NFD normalization (`resolve_existing_file`).

**convert_to_pdf** — three-step pipeline in `converter.py`:
1. `markdown_to_html()` — markdown-it-py (commonmark preset + table/strikethrough rules) + mdit-py-plugins (tasklists, frontmatter) + Pygments syntax highlighting
2. `build_html_document()` — wraps HTML body in a full document with GitHub-like CSS from `styles.py`
3. `html_to_pdf_playwright()` or `html_to_pdf_weasyprint()` — writes HTML to a temp file, loads via `file://` URL, generates PDF

### Key Module Boundaries

- **`server.py`** — MCP server setup, tool definitions, request routing. All tool handlers run blocking I/O via `run_in_executor` to avoid blocking the asyncio event loop. Logging goes to `~/.flexberry-markitdown-mcp/server.log` (not stdout, since stdout is MCP transport).
- **`converter.py`** — Pure conversion logic (no MCP dependency). Top-level entry points: `convert_md_to_pdf(text)` and `convert_md_file_to_pdf(path)`. Chromium auto-install mirrors vscode-markdown-pdf behavior (`ensure_chromium`).
- **`styles.py`** — `DEFAULT_PDF_STYLES` (GitHub-like CSS) and `get_pygments_css()` (auto-generated from Pygments formatter, cached).

### Two PDF Backends

- **Playwright** (default) — headless Chromium, auto-downloaded on first use. Supports JS-rendered content (Mermaid, PlantUML). Has header/footer with page numbers.
- **WeasyPrint** (optional, `pip install ...[weasyprint]`) — pure Python, no browser. No JS support. Used in CI for lightweight testing.

Backend selection is a string arg (`"playwright"` / `"weasyprint"`), validated in `convert_md_to_pdf`. Playwright-specific options (`display_header_footer`) are stripped when calling WeasyPrint.

### File Safety Patterns

- Atomic write: temp file with UUID suffix → `replace()` on success, cleanup on failure
- Auto-unique filenames: `make_unique_path` appends `(1)`, `(2)`, etc. when output exists and `overwrite=False`
- Unicode path resolution: `resolve_existing_file` tries NFC/NFD normalization on Windows

## Linting & Formatting (ruff)

Config in `ruff.toml`. Target: Python 3.10, line length 120. Rule set: E/W/F/I/B/C4/UP/SIM. Double quotes, 4-space indent. Known first-party: `flexberry_markitdown_mcp`.

## CI

`.github/workflows/ci.yml` — tests on Python 3.10/3.11/3.12, lint + coverage on 3.12. Tag push (`v*`) triggers PyPI publish + GitHub Release.
