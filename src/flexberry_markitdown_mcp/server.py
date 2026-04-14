#!/usr/bin/env python3
"""
MCP Server for converting files to Markdown using MarkItDown.

Features:
- Converts various file formats to Markdown
- Supports Cyrillic characters in documents and filenames
- Cross-platform (Windows/Linux)
- Handles large files by saving to disk instead of returning in context
"""

import asyncio
import logging
import sys
import unicodedata
import uuid
from pathlib import Path

# Import version from package
try:
    from . import __version__
except ImportError:
    __version__ = "1.0.0"

# Ensure UTF-8 encoding for stdin/stdout/stderr (important for Windows)
if sys.platform == "win32":
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import contextlib

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

# Import MarkItDown
try:
    from markitdown import MarkItDown
except ImportError:
    logger.error("MarkItDown not installed. Run: pip install markitdown")
    raise

# Create server instance
server = Server("flexberry-markitdown-mcp")
markitdown = MarkItDown()

# Supported file extensions
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


def get_supported_extensions_description() -> str:
    """Return a human-readable description of supported formats."""
    return """
Supported file formats:
- Documents: PDF, DOCX, DOC, PPTX, PPT, XLSX, XLS
- Web: HTML, HTM, XML, URL
- Data: CSV, JSON
- Text: MD, RST, TXT
- Images (with OCR): PNG, JPG, JPEG, GIF, BMP, TIFF, WEBP
- Audio (with transcription): MP3, WAV, M4A, OGG, FLAC
- Archives: ZIP
- E-books: EPUB
""".strip()


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

    Args:
        file_path: The requested file path (may be in any Unicode form)

    Returns:
        Path to the existing file

    Raises:
        FileNotFoundError: If no matching file is found
        ValueError: If multiple files match (ambiguous)
    """
    requested = Path(file_path)

    # First, try direct check - this works for most cases
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

        # Check if names match in any normalization form
        is_match = child_name == requested_name or child_nfc == requested_nfc or child_nfd == requested_nfd

        if is_match:
            matches.append(child)

    if len(matches) == 1:
        logger.info(f"resolve_existing_file: Found match: {matches[0]}")
        return matches[0]
    elif len(matches) == 0:
        raise FileNotFoundError(
            f"File does not exist: {requested}\n"
            f"Direct path check: {file_path} → {requested} → exists={requested.exists()}\n"
            f"Parent directory: {parent}\n"
            f"Files in parent: {[f.name for f in parent.iterdir() if f.is_file()]}"
        )
    else:
        raise ValueError(
            f"Ambiguous match for '{requested_name}' in {parent}:\n" + "\n".join(f"  - {m}" for m in matches)
        )


def normalize_path(file_path: str) -> Path:
    """
    Normalize file path for cross-platform compatibility.

    Handles both Windows and Linux paths, including paths with Cyrillic characters.

    In Python 3, paths are Unicode by default and work correctly on Windows.
    No manual encoding/decoding is needed - pathlib handles this properly.
    """
    # Expand user home directory (~)
    path = Path(file_path).expanduser()

    # Resolve to absolute path
    path = path.resolve()

    return path


def generate_output_path(input_path: Path, suffix: str = "_converted") -> Path:
    """
    Generate output path for the converted markdown file.
    The output file will be placed next to the original with .md extension.
    Uses pathlib for proper Unicode handling on Windows.
    """
    # Use pathlib methods for proper path construction
    # This handles Unicode filenames (including Cyrillic) correctly on all platforms
    # Replace original extension with .md
    return input_path.parent / f"{input_path.stem}.md"


def make_unique_path(target: Path) -> Path:
    """
    Generate a unique path by adding (1), (2), etc. if file already exists.
    Uses pathlib for proper Unicode handling.
    """
    if not target.exists():
        return target

    for i in range(1, 10000):
        candidate = target.with_name(f"{target.stem} ({i}){target.suffix}")
        if not candidate.exists():
            return candidate

    raise RuntimeError("Не удалось подобрать уникальное имя файла")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="convert_to_markdown",
            description="""Convert a file to Markdown format using MarkItDown.

The converted file is saved to disk next to the original file with .md extension.
This is designed for large files that cannot fit in LLM context.

IMPORTANT: Always use ABSOLUTE paths when calling this tool. Relative paths will be resolved
from the server's working directory, not the caller's directory.

Features:
- Automatically handles Unicode/Cyrillic filenames on Windows
- Uses atomic write pattern (temp file + rename) for safety
- Auto-unique filenames if target exists (adds (1), (2), etc.)
- Supports overwrite flag to replace existing files

"""
            + get_supported_extensions_description(),
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "ABSOLUTE path to the file to convert. Supports Cyrillic characters in paths. Example: C:\\Users\\user\\documents\\файл.docx or /home/user/documents/file.docx",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Optional custom output path. If not specified, saves next to the original file with .md extension.",
                    },
                    "overwrite": {
                        "type": "boolean",
                        "description": "Overwrite existing output file if it exists. Default: false. If false and file exists, auto-unique name is generated (adds (1), (2), etc.).",
                        "default": False,
                    },
                },
                "required": ["file_path"],
            },
        ),
        Tool(
            name="get_supported_formats",
            description="Get a list of supported file formats for conversion.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="check_file_exists",
            description="Check if a file exists and get its information. Use ABSOLUTE paths.",
            inputSchema={
                "type": "object",
                "properties": {"file_path": {"type": "string", "description": "ABSOLUTE path to the file to check."}},
                "required": ["file_path"],
            },
        ),
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


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    logger.info(f"Tool called: {name} with arguments: {arguments}")

    if name == "get_supported_formats":
        return [TextContent(type="text", text=get_supported_extensions_description())]

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
                supported_mark = "✓" if is_supported else ""
                # Show codepoints for filenames with non-ASCII characters
                name_codepoints = ""
                if any(ord(c) > 127 for c in f.name):
                    name_codepoints = f" [{dump_codepoints(f.name)}]"
                result_lines.append(f"{file_type} {f.name}{name_codepoints} ({size:,} bytes) {supported_mark}")

            return [TextContent(type="text", text="\n".join(result_lines))]

        except Exception as e:
            logger.exception(f"Error listing directory: {directory_path}")
            return [TextContent(type="text", text=f"Error listing directory: {str(e)}")]

    if name == "check_file_exists":
        file_path = arguments.get("file_path", "")

        if not file_path:
            return [TextContent(type="text", text="Error: file_path is required.")]

        try:
            # Resolve file path (handles Unicode normalization issues)
            path = resolve_existing_file(file_path)

            if not path.is_file():
                return [TextContent(type="text", text=f"Path is not a file: {path}")]

            size = path.stat().st_size
            ext = path.suffix.lower()
            is_supported = ext in SUPPORTED_EXTENSIONS

            return [
                TextContent(
                    type="text",
                    text=f"""File: {path}
Size: {size:,} bytes ({size / 1024 / 1024:.2f} MB)
Extension: {ext}
Supported: {"Yes" if is_supported else "No"}""",
                )
            ]

        except FileNotFoundError as e:
            logger.exception(f"File not found: {file_path}")
            return [TextContent(type="text", text=f"File does not exist: {str(e)}")]

        except Exception as e:
            logger.exception(f"Error checking file: {file_path}")
            return [TextContent(type="text", text=f"Error checking file: {str(e)}")]

    if name == "convert_to_markdown":
        file_path = arguments.get("file_path", "")
        output_path_arg = arguments.get("output_path", "")
        overwrite = arguments.get("overwrite", False)

        if not file_path:
            return [TextContent(type="text", text="Error: file_path is required.")]

        try:
            # Resolve input file path (handles Unicode normalization issues)
            input_path = resolve_existing_file(file_path)

            # Check extension
            ext = input_path.suffix.lower()
            if ext not in SUPPORTED_EXTENSIONS:
                return [
                    TextContent(
                        type="text",
                        text=f"Error: Unsupported file format '{ext}'.\n\n{get_supported_extensions_description()}",
                    )
                ]

            # Determine output path
            if output_path_arg:
                output_path = normalize_path(output_path_arg)
            else:
                output_path = generate_output_path(input_path)

            # Auto-unique path if file exists and overwrite is False
            if not overwrite and output_path.exists():
                output_path = make_unique_path(output_path)

            # Get input file size for logging
            input_size = input_path.stat().st_size
            logger.info(f"Converting file: {input_path} ({input_size:,} bytes)")

            # Convert the file using MarkItDown
            # Run in executor to avoid blocking the event loop for large files
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, markitdown.convert, str(input_path))

            # Get the markdown content
            markdown_content = result.text_content

            # Write to output file using atomic write pattern:
            # 1. Write to temp file first
            # 2. Rename to final path (atomic on same filesystem)
            # This prevents partial/corrupt files if conversion fails
            temp_path = output_path.parent / f".{output_path.stem}.{uuid.uuid4().hex}.tmp"
            try:
                # Write to temp file with UTF-8 encoding
                temp_path.write_text(markdown_content, encoding="utf-8", newline="")

                # Atomic rename to final path
                temp_path.replace(output_path)
            finally:
                # Clean up temp file if it still exists
                if temp_path.exists():
                    with contextlib.suppress(OSError):
                        temp_path.unlink()

            output_size = output_path.stat().st_size

            logger.info(f"Conversion complete: {output_path} ({output_size:,} bytes)")

            # Return structured result with overwrite flag
            return [
                TextContent(
                    type="text",
                    text=f"""Conversion successful!

Input file: {input_path}
Input size: {input_size:,} bytes ({input_size / 1024 / 1024:.2f} MB)

Output file: {output_path}
Output size: {output_size:,} bytes ({output_size / 1024 / 1024:.2f} MB)
Overwritten: {overwrite}

The converted Markdown file has been saved to disk and is ready for use.""",
                )
            ]

        except Exception as e:
            logger.exception(f"Error converting file: {file_path}")
            return [
                TextContent(type="text", text=f"Error converting file: {str(e)}\n\nCheck the log file at: {log_file}")
            ]

    return [TextContent(type="text", text=f"Error: Unknown tool '{name}'")]


async def run_server():
    """Run the MCP server."""
    logger.info("Starting Flexberry MarkItDown MCP Server")
    logger.info(f"Platform: {sys.platform}")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Current working directory: {Path.cwd()}")
    logger.info(f"File system encoding: {sys.getfilesystemencoding()}")

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
