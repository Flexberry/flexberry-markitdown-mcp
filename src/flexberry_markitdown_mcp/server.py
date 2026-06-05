#!/usr/bin/env python3
"""
MCP Server for converting files to Markdown (via MarkItDown) and Markdown to PDF.

Features:
- Converts various file formats to Markdown using MarkItDown
- Converts Markdown files to PDF via Playwright (headless Chromium, auto-download)
- Optional WeasyPrint backend (pure Python, no browser)
- Supports Cyrillic characters in documents and filenames
- Cross-platform (Windows/Linux)
- Handles large files by saving to disk instead of returning in context

Uses:
  - Microsoft MarkItDown (https://github.com/microsoft/markitdown) — any-format → MD
  - Inspired by vscode-markdown-pdf (https://github.com/showzs/vscode-markdown-pdf) — MD → PDF approach
"""

import asyncio
import contextlib
import logging
import sys
import unicodedata
import uuid
from pathlib import Path

# Import version from package
try:
    from . import __version__
except ImportError:
    __version__ = "2.0.0"

# Ensure UTF-8 encoding for stdin/stdout/stderr (important for Windows)
if sys.platform == "win32":
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from mcp.server import InitializationOptions, NotificationOptions, Server, stdio
from mcp.types import TextContent, Tool

# Configure logging to file (since stdout is used for MCP communication)
log_dir = Path.home() / ".flexberry-markitdown-mcp"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "server.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file, encoding="utf-8")],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# MarkItDown (PDF → MD)
# ---------------------------------------------------------------------------

try:
    from markitdown import MarkItDown
except ImportError:
    logger.error("MarkItDown not installed. Run: pip install markitdown")
    raise

server = Server("flexberry-markitdown-mcp")
markitdown = MarkItDown()

# ---------------------------------------------------------------------------
# Supported extensions for MarkItDown conversion
# ---------------------------------------------------------------------------

SUPPORTED_EXTENSIONS = {
    # Documents
    ".pdf",
    ".docx",
    ".doc",
    ".pptx",
    ".ppt",
    ".xlsx",
    ".xls",
    # Web
    ".html",
    ".htm",
    ".xml",
    ".url",
    # Data
    ".csv",
    ".json",
    # Code/Text
    ".md",
    ".rst",
    ".txt",
    # Images (with OCR)
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".tiff",
    ".webp",
    # Audio (with transcription)
    ".mp3",
    ".wav",
    ".m4a",
    ".ogg",
    ".flac",
    # Archives
    ".zip",
    # E-books
    ".epub",
}

# PDF backend availability flags
_PLAYWRIGHT_AVAILABLE = False
_WEASYPRINT_AVAILABLE = False

try:
    import playwright  # noqa: F401

    _PLAYWRIGHT_AVAILABLE = True
except ImportError:
    pass

try:
    import weasyprint  # noqa: F401

    _WEASYPRINT_AVAILABLE = True
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------


def get_supported_extensions_description() -> str:
    """Return a human-readable description of supported formats for MarkItDown."""
    return """
Supported file formats for convert_to_markdown:
- Documents: PDF, DOCX, DOC, PPTX, PPT, XLSX, XLS
- Web: HTML, HTM, XML, URL
- Data: CSV, JSON
- Text: MD, RST, TXT
- Images (with OCR): PNG, JPG, JPEG, GIF, BMP, TIFF, WEBP
- Audio (with transcription): MP3, WAV, M4A, OGG, FLAC
- Archives: ZIP
- E-books: EPUB
""".strip()


def get_pdf_backend_description() -> str:
    """Return a description of available PDF backends."""
    lines = ["Available PDF backends for convert_to_pdf:"]

    if _PLAYWRIGHT_AVAILABLE:
        lines.append(
            "- playwright (DEFAULT): Headless Chromium. Supports JS-rendered content "
            "(Mermaid diagrams, PlantUML, etc.). Chromium is auto-downloaded on first use."
        )
    else:
        lines.append("- playwright: NOT INSTALLED. Install with: pip install flexberry-markitdown-mcp")

    if _WEASYPRINT_AVAILABLE:
        lines.append(
            "- weasyprint: Pure-Python renderer. No browser required. "
            "Does NOT support JS-rendered content. Good lightweight alternative."
        )
    else:
        lines.append("- weasyprint: NOT INSTALLED. Install with: pip install flexberry-markitdown-mcp[weasyprint]")

    lines.append("Current default backend: playwright")
    return "\n".join(lines)


def dump_codepoints(s: str) -> str:
    """
    Return a string representation of Unicode codepoints for debugging.
    Example: "Кейсы" -> "U+041A U+0435 U+0439 U+0441 U+044B"
    """
    return " ".join(f"U+{ord(ch):04X}" for ch in s)


def resolve_existing_file(file_path: str) -> Path:
    """
    Resolve a file path that may have Unicode normalization issues.

    On Windows, filenames can be stored in different Unicode forms (NFC vs NFD).
    This function tries to find the actual file by normalizing names and comparing.
    """
    requested = Path(file_path)

    if requested.exists():
        return requested

    parent = requested.parent
    if not parent.is_dir():
        raise FileNotFoundError(f"Directory does not exist: {parent}\nRequested path: {requested}")

    requested_name = requested.name
    requested_nfc = unicodedata.normalize("NFC", requested_name)
    requested_nfd = unicodedata.normalize("NFD", requested_name)

    matches = []
    for child in parent.iterdir():
        if not child.is_file():
            continue
        child_name = child.name
        child_nfc = unicodedata.normalize("NFC", child_name)
        child_nfd = unicodedata.normalize("NFD", child_name)

        is_match = child_name == requested_name or child_nfc == requested_nfc or child_nfd == requested_nfd

        if is_match:
            matches.append(child)

    if len(matches) == 1:
        logger.info(f"resolve_existing_file: Found match: {matches[0]}")
        return matches[0]
    elif len(matches) == 0:
        raise FileNotFoundError(
            f"File does not exist: {requested}\n"
            f"Direct path check: {file_path} -> {requested} -> exists={requested.exists()}\n"
            f"Parent directory: {parent}\n"
            f"Files in parent: {[f.name for f in parent.iterdir() if f.is_file()]}"
        )
    else:
        raise ValueError(
            f"Ambiguous match for '{requested_name}' in {parent}:\n" + "\n".join(f"  - {m}" for m in matches)
        )


def normalize_path(file_path: str) -> Path:
    """Normalize file path for cross-platform compatibility."""
    path = Path(file_path).expanduser()
    path = path.resolve()
    return path


def generate_output_path(input_path: Path, ext: str = ".md") -> Path:
    """Generate output path for the converted file."""
    return input_path.parent / f"{input_path.stem}{ext}"


def make_unique_path(target: Path) -> Path:
    """Generate a unique path by adding (1), (2), etc. if file already exists."""
    if not target.exists():
        return target

    for i in range(1, 10000):
        candidate = target.with_name(f"{target.stem} ({i}){target.suffix}")
        if not candidate.exists():
            return candidate

    raise RuntimeError("Could not generate a unique file name")


# ---------------------------------------------------------------------------
# MCP Tool definitions
# ---------------------------------------------------------------------------


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        # ── convert_to_markdown ──────────────────────────────────────────
        Tool(
            name="convert_to_markdown",
            description=(
                "Convert a file to Markdown format using MarkItDown.\n\n"
                "The converted file is saved to disk next to the original file with .md extension.\n"
                "This is designed for large files that cannot fit in LLM context.\n\n"
                "IMPORTANT: Always use ABSOLUTE paths when calling this tool.\n\n"
                "Features:\n"
                "- Automatically handles Unicode/Cyrillic filenames on Windows\n"
                "- Uses atomic write pattern (temp file + rename) for safety\n"
                "- Auto-unique filenames if target exists (adds (1), (2), etc.)\n"
                "- Supports overwrite flag to replace existing files\n\n"
            )
            + get_supported_extensions_description(),
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "ABSOLUTE path to the file to convert. Supports Cyrillic characters in paths.",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Optional custom output path. If not specified, saves next to the original file with .md extension.",
                    },
                    "overwrite": {
                        "type": "boolean",
                        "description": "Overwrite existing output file if it exists. Default: false.",
                        "default": False,
                    },
                },
                "required": ["file_path"],
            },
        ),
        # ── convert_to_pdf ──────────────────────────────────────────────
        Tool(
            name="convert_to_pdf",
            description=(
                "Convert a Markdown file to PDF.\n\n"
                "Default backend: Playwright (headless Chromium) — same approach as vscode-markdown-pdf.\n"
                "Chromium is auto-downloaded on first use, so no manual setup needed.\n"
                "Supports JavaScript-rendered content (Mermaid diagrams, PlantUML, etc.).\n\n"
                "Optional backend: WeasyPrint — pure Python, no browser required.\n"
                "Install with: pip install flexberry-markitdown-mcp[weasyprint]\n\n"
                "The PDF is saved to disk next to the original file (or at a custom output_path).\n\n"
                "IMPORTANT: Always use ABSOLUTE paths when calling this tool.\n\n"
                "Features:\n"
                "- GitHub-flavored Markdown (tables, task lists, strikethrough)\n"
                "- Syntax highlighting in code blocks (via Pygments)\n"
                "- Configurable page format (A4, Letter, etc.) and margins\n"
                "- Custom CSS injection\n"
                "- Header/footer with page numbers\n\n"
            )
            + get_pdf_backend_description(),
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "ABSOLUTE path to the Markdown (.md) file to convert to PDF.",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Optional custom output path for the PDF. If not specified, saves next to the original file with .pdf extension.",
                    },
                    "backend": {
                        "type": "string",
                        "enum": ["playwright", "weasyprint"],
                        "description": "PDF generation backend. 'playwright' (default) or 'weasyprint'.",
                        "default": "playwright",
                    },
                    "overwrite": {
                        "type": "boolean",
                        "description": "Overwrite existing output file if it exists. Default: false.",
                        "default": False,
                    },
                    "custom_css": {
                        "type": "string",
                        "description": "Additional CSS to inject into the PDF. Overrides default styles for matching selectors.",
                    },
                    "include_default_styles": {
                        "type": "boolean",
                        "description": "Include built-in GitHub-like styles. Default: true. Set to false if providing full custom CSS.",
                        "default": True,
                    },
                    "format": {
                        "type": "string",
                        "description": "Paper format: A4, A3, Letter, Legal, Tabloid, etc. Default: A4.",
                        "default": "A4",
                    },
                    "margin_top": {
                        "type": "string",
                        "description": "Top margin. Default: 1.5cm.",
                        "default": "1.5cm",
                    },
                    "margin_bottom": {
                        "type": "string",
                        "description": "Bottom margin. Default: 1cm.",
                        "default": "1cm",
                    },
                    "margin_left": {
                        "type": "string",
                        "description": "Left margin. Default: 1cm.",
                        "default": "1cm",
                    },
                    "margin_right": {
                        "type": "string",
                        "description": "Right margin. Default: 1cm.",
                        "default": "1cm",
                    },
                    "print_background": {
                        "type": "boolean",
                        "description": "Print background colors and images. Default: true.",
                        "default": True,
                    },
                    "display_header_footer": {
                        "type": "boolean",
                        "description": "Display header and footer in PDF. Default: true.",
                        "default": True,
                    },
                },
                "required": ["file_path"],
            },
        ),
        # ── get_supported_formats ────────────────────────────────────────
        Tool(
            name="get_supported_formats",
            description="Get a list of supported file formats for conversion.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        # ── check_file_exists ────────────────────────────────────────────
        Tool(
            name="check_file_exists",
            description="Check if a file exists and get its information. Use ABSOLUTE paths.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "ABSOLUTE path to the file to check.",
                    }
                },
                "required": ["file_path"],
            },
        ),
        # ── list_directory ───────────────────────────────────────────────
        Tool(
            name="list_directory",
            description="List files in a directory. Use this to verify file paths and see available files.",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory_path": {
                        "type": "string",
                        "description": "ABSOLUTE path to the directory to list. Leave empty to list current working directory.",
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Optional glob pattern to filter files (e.g., '*.docx', '*.pdf').",
                    },
                },
                "required": [],
            },
        ),
    ]


# ---------------------------------------------------------------------------
# MCP Tool handler
# ---------------------------------------------------------------------------


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    logger.info(f"Tool called: {name} with arguments: {arguments}")

    # ── get_supported_formats ────────────────────────────────────────────
    if name == "get_supported_formats":
        return [
            TextContent(
                type="text",
                text=get_supported_extensions_description() + "\n\n" + get_pdf_backend_description(),
            )
        ]

    # ── list_directory ───────────────────────────────────────────────────
    if name == "list_directory":
        directory_path = arguments.get("directory_path", "")
        pattern = arguments.get("pattern", "*")

        try:
            if directory_path:
                dir_path = Path(directory_path).expanduser().resolve()
            else:
                dir_path = Path.cwd()

            if not dir_path.exists():
                return [TextContent(type="text", text=f"Directory does not exist: {dir_path}")]

            if not dir_path.is_dir():
                return [TextContent(type="text", text=f"Path is not a directory: {dir_path}")]

            files = list(dir_path.glob(pattern))

            result_lines = [f"Directory: {dir_path}", f"Pattern: {pattern}", f"Found {len(files)} items:", ""]

            for f in sorted(files, key=lambda x: (not x.is_file(), x.name.lower())):
                file_type = "[DIR]" if f.is_dir() else "[FILE]"
                size = f.stat().st_size if f.is_file() else 0
                ext = f.suffix.lower() if f.suffix else ""
                is_supported = ext in SUPPORTED_EXTENSIONS if f.is_file() else False
                is_md = ext == ".md" if f.is_file() else False
                supported_mark = "✓" if is_supported else ("📄" if is_md else "")
                name_codepoints = ""
                if any(ord(c) > 127 for c in f.name):
                    name_codepoints = f" [{dump_codepoints(f.name)}]"
                result_lines.append(f"{file_type} {f.name}{name_codepoints} ({size:,} bytes) {supported_mark}")

            return [TextContent(type="text", text="\n".join(result_lines))]

        except Exception as e:
            logger.exception(f"Error listing directory: {directory_path}")
            return [TextContent(type="text", text=f"Error listing directory: {str(e)}")]

    # ── check_file_exists ────────────────────────────────────────────────
    if name == "check_file_exists":
        file_path = arguments.get("file_path", "")

        if not file_path:
            return [TextContent(type="text", text="Error: file_path is required.")]

        try:
            path = resolve_existing_file(file_path)

            if not path.is_file():
                return [TextContent(type="text", text=f"Path is not a file: {path}")]

            size = path.stat().st_size
            ext = path.suffix.lower()
            is_supported = ext in SUPPORTED_EXTENSIONS
            is_md = ext == ".md"

            return [
                TextContent(
                    type="text",
                    text=(
                        f"File: {path}\n"
                        f"Size: {size:,} bytes ({size / 1024 / 1024:.2f} MB)\n"
                        f"Extension: {ext}\n"
                        f"Supported (→MD): {'Yes' if is_supported else 'No'}\n"
                        f"Can convert to PDF: {'Yes' if is_md else 'No'}"
                    ),
                )
            ]

        except FileNotFoundError as e:
            logger.exception(f"File not found: {file_path}")
            return [TextContent(type="text", text=f"File does not exist: {str(e)}")]
        except Exception as e:
            logger.exception(f"Error checking file: {file_path}")
            return [TextContent(type="text", text=f"Error checking file: {str(e)}")]

    # ── convert_to_markdown ──────────────────────────────────────────────
    if name == "convert_to_markdown":
        file_path = arguments.get("file_path", "")
        output_path_arg = arguments.get("output_path", "")
        overwrite = arguments.get("overwrite", False)

        if not file_path:
            return [TextContent(type="text", text="Error: file_path is required.")]

        try:
            input_path = resolve_existing_file(file_path)

            ext = input_path.suffix.lower()
            if ext not in SUPPORTED_EXTENSIONS:
                return [
                    TextContent(
                        type="text",
                        text=f"Error: Unsupported file format '{ext}'.\n\n{get_supported_extensions_description()}",
                    )
                ]

            if output_path_arg:
                output_path = normalize_path(output_path_arg)
            else:
                output_path = generate_output_path(input_path, ".md")

            if not overwrite and output_path.exists():
                output_path = make_unique_path(output_path)

            input_size = input_path.stat().st_size
            logger.info(f"Converting file: {input_path} ({input_size:,} bytes)")

            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, markitdown.convert, str(input_path))

            markdown_content = result.text_content

            temp_path = output_path.parent / f".{output_path.stem}.{uuid.uuid4().hex}.tmp"
            try:
                temp_path.write_text(markdown_content, encoding="utf-8", newline="")
                temp_path.replace(output_path)
            finally:
                if temp_path.exists():
                    with contextlib.suppress(OSError):
                        temp_path.unlink()

            output_size = output_path.stat().st_size
            logger.info(f"Conversion complete: {output_path} ({output_size:,} bytes)")

            return [
                TextContent(
                    type="text",
                    text=(
                        f"Conversion successful!\n\n"
                        f"Input file: {input_path}\n"
                        f"Input size: {input_size:,} bytes ({input_size / 1024 / 1024:.2f} MB)\n\n"
                        f"Output file: {output_path}\n"
                        f"Output size: {output_size:,} bytes ({output_size / 1024 / 1024:.2f} MB)\n"
                        f"Overwritten: {overwrite}\n\n"
                        f"The converted Markdown file has been saved to disk and is ready for use."
                    ),
                )
            ]

        except Exception as e:
            logger.exception(f"Error converting file: {file_path}")
            return [
                TextContent(
                    type="text",
                    text=f"Error converting file: {str(e)}\n\nCheck the log file at: {log_file}",
                )
            ]

    # ── convert_to_pdf ──────────────────────────────────────────────────
    if name == "convert_to_pdf":
        file_path = arguments.get("file_path", "")
        output_path_arg = arguments.get("output_path", "")
        backend = arguments.get("backend", "playwright")
        overwrite = arguments.get("overwrite", False)
        custom_css = arguments.get("custom_css", "")
        include_default_styles = arguments.get("include_default_styles", True)

        # Page options
        format_ = arguments.get("format", "A4")
        margin_top = arguments.get("margin_top", "1.5cm")
        margin_bottom = arguments.get("margin_bottom", "1cm")
        margin_left = arguments.get("margin_left", "1cm")
        margin_right = arguments.get("margin_right", "1cm")
        print_background = arguments.get("print_background", True)
        display_header_footer = arguments.get("display_header_footer", True)

        if not file_path:
            return [TextContent(type="text", text="Error: file_path is required.")]

        try:
            input_path = resolve_existing_file(file_path)

            ext = input_path.suffix.lower()
            if ext not in {".md", ".markdown", ".mdown", ".mkd", ".mkdn"}:
                return [
                    TextContent(
                        type="text",
                        text=(f"Error: convert_to_pdf only supports Markdown files (.md, .markdown). Got: '{ext}'"),
                    )
                ]

            if output_path_arg:
                output_path = normalize_path(output_path_arg)
            else:
                output_path = generate_output_path(input_path, ".pdf")

            if not overwrite and output_path.exists():
                output_path = make_unique_path(output_path)

            input_size = input_path.stat().st_size
            logger.info(f"Converting MD to PDF: {input_path} -> {output_path} (backend={backend})")

            # Import the converter lazily so that the server can start even
            # if only one backend is installed
            from .converter import convert_md_file_to_pdf

            # Build kwargs for the converter
            converter_kwargs: dict = {
                "backend": backend,
                "custom_css": custom_css,
                "include_default_styles": include_default_styles,
                "title": input_path.stem,
                "format": format_,
                "margin_top": margin_top,
                "margin_bottom": margin_bottom,
                "margin_left": margin_left,
                "margin_right": margin_right,
                "print_background": print_background,
            }

            # Playwright-specific options
            if backend == "playwright":
                converter_kwargs["display_header_footer"] = display_header_footer

            # Run conversion in executor to avoid blocking the event loop
            loop = asyncio.get_running_loop()
            result_path = await loop.run_in_executor(
                None,
                lambda: convert_md_file_to_pdf(
                    input_path=input_path,
                    output_path=output_path,
                    **converter_kwargs,
                ),
            )

            output_size = result_path.stat().st_size
            logger.info(f"PDF conversion complete: {result_path} ({output_size:,} bytes)")

            return [
                TextContent(
                    type="text",
                    text=(
                        f"PDF conversion successful!\n\n"
                        f"Input file: {input_path}\n"
                        f"Input size: {input_size:,} bytes ({input_size / 1024 / 1024:.2f} MB)\n\n"
                        f"Output file: {result_path}\n"
                        f"Output size: {output_size:,} bytes ({output_size / 1024 / 1024:.2f} MB)\n"
                        f"Backend: {backend}\n"
                        f"Overwritten: {overwrite}\n\n"
                        f"The PDF file has been saved to disk and is ready for use."
                    ),
                )
            ]

        except ImportError as e:
            logger.exception(f"Missing dependency for PDF conversion: {e}")
            return [
                TextContent(
                    type="text",
                    text=(
                        f"Error: Missing dependency for PDF conversion.\n{str(e)}\n\n{get_pdf_backend_description()}"
                    ),
                )
            ]
        except Exception as e:
            logger.exception(f"Error converting file to PDF: {file_path}")
            return [
                TextContent(
                    type="text",
                    text=f"Error converting file to PDF: {str(e)}\n\nCheck the log file at: {log_file}",
                )
            ]

    return [TextContent(type="text", text=f"Error: Unknown tool '{name}'")]


# ---------------------------------------------------------------------------
# Server entry point
# ---------------------------------------------------------------------------


async def run_server():
    """Run the MCP server."""
    logger.info("Starting Flexberry MarkItDown MCP Server (with PDF export)")
    logger.info(f"Platform: {sys.platform}")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Current working directory: {Path.cwd()}")
    logger.info(f"File system encoding: {sys.getfilesystemencoding()}")
    logger.info(f"Playwright available: {_PLAYWRIGHT_AVAILABLE}")
    logger.info(f"WeasyPrint available: {_WEASYPRINT_AVAILABLE}")

    # Run the server using stdio transport
    logger.info("About to create stdio_server")
    try:
        async with stdio.stdio_server() as (read_stream, write_stream):
            logger.info("stdio_server created, about to call server.run")
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="flexberry-markitdown-mcp",
                    server_version=__version__,
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
            logger.info("server.run completed")
    except Exception as e:
        logger.exception(f"Error in run_server: {e}")
        raise


def main():
    """Main entry point for the MCP server."""
    try:
        logger.info("About to run asyncio.run(run_server())")
        asyncio.run(run_server())
        logger.info("asyncio.run(run_server()) completed")
    except Exception as e:
        logger.exception(f"Error in main: {e}")
        raise


if __name__ == "__main__":
    main()
