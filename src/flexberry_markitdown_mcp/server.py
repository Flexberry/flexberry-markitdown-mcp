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
from pathlib import Path

# Ensure UTF-8 encoding for stdin/stdout/stderr (important for Windows)
if sys.platform == "win32":
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from mcp.server import NotificationOptions, Server, InitializationOptions, stdio
from mcp.types import TextContent, Tool

# Configure logging to file (since stdout is used for MCP communication)
log_dir = Path.home() / ".flexberry-markitdown-mcp"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "server.log"

logging.basicConfig(
    level=logging.DEBUG,  # Increased logging level for debugging
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8')
    ]
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
    '.pdf', '.docx', '.doc', '.pptx', '.ppt', '.xlsx', '.xls',
    # Web
    '.html', '.htm', '.xml', '.url',
    # Data
    '.csv', '.json',
    # Code/Text
    '.md', '.rst', '.txt',
    # Images (with OCR)
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp',
    # Audio (with transcription)
    '.mp3', '.wav', '.m4a', '.ogg', '.flac',
    # Archives
    '.zip',
    # E-books
    '.epub',
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


def normalize_path(file_path: str) -> Path:
    """
    Normalize file path for cross-platform compatibility.
    Handles both Windows and Linux paths, including paths with Cyrillic characters.
    """
    logger.debug(f"normalize_path input: '{file_path}' (type: {type(file_path)})")
    logger.debug(f"normalize_path repr: {repr(file_path)}")

    # Expand user home directory (~)
    path = Path(file_path).expanduser()
    logger.debug(f"After expanduser: '{path}'")

    # Resolve to absolute path
    path = path.resolve()
    logger.debug(f"After resolve: '{path}'")

    # Check if path exists (for debugging)
    exists = path.exists()
    logger.debug(f"Path exists: {exists}")

    if not exists:
        # Try to list parent directory for debugging
        parent = path.parent
        if parent.exists():
            logger.debug(f"Parent directory exists: {parent}")
            try:
                files = list(parent.iterdir())
                logger.debug(f"Files in parent: {[f.name for f in files[:10]]}")
            except Exception as e:
                logger.debug(f"Error listing parent: {e}")

    return path


def generate_output_path(input_path: Path) -> Path:
    """
    Generate output path for the converted markdown file.
    The output file will be placed next to the original with .md extension.
    """
    # Get the directory and base name
    directory = input_path.parent
    base_name = input_path.stem

    # Create output path with .md extension
    output_path = directory / f"{base_name}.md"

    return output_path


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

""" + get_supported_extensions_description(),
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "ABSOLUTE path to the file to convert. Supports Cyrillic characters in paths. Example: C:\\Users\\user\\documents\\file.docx or /home/user/documents/file.docx"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Optional custom output path. If not specified, saves next to the original file with .md extension."
                    },
                    "overwrite": {
                        "type": "boolean",
                        "description": "Overwrite existing output file if it exists. Default: false.",
                        "default": False
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="get_supported_formats",
            description="Get a list of supported file formats for conversion.",
            inputSchema={
                "type": "object",
                "properties": {},
            }
        ),
        Tool(
            name="check_file_exists",
            description="Check if a file exists and get its information. Use ABSOLUTE paths.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "ABSOLUTE path to the file to check."
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="list_directory",
            description="List files in a directory. Use this to verify file paths and see available files.",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory_path": {
                        "type": "string",
                        "description": "ABSOLUTE path to the directory to list. Leave empty to list current working directory."
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Optional glob pattern to filter files (e.g., '*.docx', '*.pdf')."
                    }
                },
                "required": []
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    logger.info(f"Tool called: {name} with arguments: {arguments}")

    if name == "get_supported_formats":
        return [TextContent(
            type="text",
            text=get_supported_extensions_description()
        )]

    if name == "list_directory":
        directory_path = arguments.get("directory_path", "")
        pattern = arguments.get("pattern", "*")

        try:
            if directory_path:
                dir_path = Path(directory_path).expanduser().resolve()
            else:
                dir_path = Path.cwd()

            logger.debug(f"Listing directory: {dir_path}")

            if not dir_path.exists():
                return [TextContent(
                    type="text",
                    text=f"Directory does not exist: {dir_path}"
                )]

            if not dir_path.is_dir():
                return [TextContent(
                    type="text",
                    text=f"Path is not a directory: {dir_path}"
                )]

            files = list(dir_path.glob(pattern))

            result_lines = [f"Directory: {dir_path}", f"Pattern: {pattern}", f"Found {len(files)} items:", ""]

            for f in sorted(files, key=lambda x: (not x.is_file(), x.name.lower())):
                file_type = "[DIR]" if f.is_dir() else "[FILE]"
                size = f.stat().st_size if f.is_file() else 0
                ext = f.suffix.lower() if f.suffix else ""
                is_supported = ext in SUPPORTED_EXTENSIONS if f.is_file() else False
                supported_mark = "✓" if is_supported else ""
                result_lines.append(f"{file_type} {f.name} ({size:,} bytes) {supported_mark}")

            return [TextContent(
                type="text",
                text="\n".join(result_lines)
            )]

        except Exception as e:
            logger.exception(f"Error listing directory: {directory_path}")
            return [TextContent(
                type="text",
                text=f"Error listing directory: {str(e)}"
            )]

    if name == "check_file_exists":
        file_path = arguments.get("file_path", "")

        if not file_path:
            return [TextContent(
                type="text",
                text="Error: file_path is required."
            )]

        try:
            path = normalize_path(file_path)

            if not path.exists():
                # Provide helpful debugging info
                parent = path.parent
                parent_exists = parent.exists()
                cwd = Path.cwd()

                debug_info = f"""File does not exist: {path}

Debug info:
- Original path: '{file_path}'
- Normalized path: '{path}'
- Parent directory: {parent}
- Parent exists: {parent_exists}
- Server working directory: {cwd}
"""
                if parent_exists:
                    try:
                        files_in_parent = [f.name for f in parent.iterdir() if f.is_file()]
                        debug_info += f"- Files in parent directory: {files_in_parent[:10]}"
                    except Exception as e:
                        debug_info += f"- Error listing parent: {e}"

                return [TextContent(
                    type="text",
                    text=debug_info
                )]

            if not path.is_file():
                return [TextContent(
                    type="text",
                    text=f"Path is not a file: {path}"
                )]

            size = path.stat().st_size
            ext = path.suffix.lower()
            is_supported = ext in SUPPORTED_EXTENSIONS

            return [TextContent(
                type="text",
                text=f"""File: {path}
Size: {size:,} bytes ({size / 1024 / 1024:.2f} MB)
Extension: {ext}
Supported: {"Yes" if is_supported else "No"}"""
            )]

        except Exception as e:
            logger.exception(f"Error checking file: {file_path}")
            return [TextContent(
                type="text",
                text=f"Error checking file: {str(e)}"
            )]

    if name == "convert_to_markdown":
        file_path = arguments.get("file_path", "")
        output_path_arg = arguments.get("output_path", "")
        overwrite = arguments.get("overwrite", False)

        if not file_path:
            return [TextContent(
                type="text",
                text="Error: file_path is required."
            )]

        try:
            # Normalize input path
            input_path = normalize_path(file_path)

            # Check if input file exists
            if not input_path.exists():
                # Provide helpful debugging info
                parent = input_path.parent
                cwd = Path.cwd()

                error_msg = f"""Error: File does not exist: {input_path}

Original path: '{file_path}'
Server working directory: {cwd}

"""
                if parent.exists():
                    try:
                        files = [f.name for f in parent.iterdir() if f.is_file()]
                        error_msg += f"Files in parent directory ({parent}):\n"
                        for f in files[:20]:
                            error_msg += f"  - {f}\n"
                    except Exception as e:
                        error_msg += f"Error listing parent directory: {e}"
                else:
                    error_msg += f"Parent directory does not exist: {parent}"

                return [TextContent(
                    type="text",
                    text=error_msg
                )]

            if not input_path.is_file():
                return [TextContent(
                    type="text",
                    text=f"Error: Path is not a file: {input_path}"
                )]

            # Check extension
            ext = input_path.suffix.lower()
            if ext not in SUPPORTED_EXTENSIONS:
                return [TextContent(
                    type="text",
                    text=f"Error: Unsupported file format '{ext}'.\n\n{get_supported_extensions_description()}"
                )]

            # Determine output path
            if output_path_arg:
                output_path = normalize_path(output_path_arg)
            else:
                output_path = generate_output_path(input_path)

            # Check if output file exists
            if output_path.exists() and not overwrite:
                return [TextContent(
                    type="text",
                    text=f"Error: Output file already exists: {output_path}\nUse overwrite=true to overwrite."
                )]

            # Get input file size for logging
            input_size = input_path.stat().st_size
            logger.info(f"Converting file: {input_path} ({input_size:,} bytes)")

            # Convert the file using MarkItDown
            # Run in executor to avoid blocking the event loop for large files
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                markitdown.convert,
                str(input_path)
            )

            # Get the markdown content
            markdown_content = result.text_content

            # Write to output file
            # Use UTF-8 encoding explicitly for Cyrillic support
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                f.write(markdown_content)

            output_size = output_path.stat().st_size

            logger.info(f"Conversion complete: {output_path} ({output_size:,} bytes)")

            return [TextContent(
                type="text",
                text=f"""Conversion successful!

Input file: {input_path}
Input size: {input_size:,} bytes ({input_size / 1024 / 1024:.2f} MB)

Output file: {output_path}
Output size: {output_size:,} bytes ({output_size / 1024 / 1024:.2f} MB)

The converted Markdown file has been saved to disk and is ready for use."""
            )]

        except Exception as e:
            logger.exception(f"Error converting file: {file_path}")
            return [TextContent(
                type="text",
                text=f"Error converting file: {str(e)}\n\nCheck the log file at: {log_file}"
            )]

    return [TextContent(
        type="text",
        text=f"Error: Unknown tool '{name}'"
    )]


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
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                )
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
