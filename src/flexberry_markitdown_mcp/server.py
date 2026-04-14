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
import os
import sys
from pathlib import Path
from typing import Optional

# Ensure UTF-8 encoding for stdin/stdout/stderr (important for Windows)
if sys.platform == "win32":
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from mcp.server import Server, InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ServerCapabilities, ToolsCapability

# Configure logging to file (since stdout is used for MCP communication)
log_dir = Path.home() / ".flexberry-markitdown-mcp"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "server.log"

logging.basicConfig(
    level=logging.INFO,
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
    # Expand user home directory (~)
    path = Path(file_path).expanduser()
    
    # Resolve to absolute path
    path = path.resolve()
    
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

""" + get_supported_extensions_description(),
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Absolute or relative path to the file to convert. Supports Cyrillic characters in paths."
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
            description="Check if a file exists and get its information.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to check."
                    }
                },
                "required": ["file_path"]
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    
    if name == "get_supported_formats":
        return [TextContent(
            type="text",
            text=get_supported_extensions_description()
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
                return [TextContent(
                    type="text",
                    text=f"File does not exist: {path}"
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
                return [TextContent(
                    type="text",
                    text=f"Error: File does not exist: {input_path}"
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


def main():
    """Main entry point for the MCP server."""
    logger.info("Starting Flexberry MarkItDown MCP Server")
    logger.info(f"Platform: {sys.platform}")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Log file: {log_file}")
    
    # Run the server using stdio transport
    async def run_server():
        initialization_options = InitializationOptions(
            server_name="flexberry-markitdown-mcp",
            server_version="1.0.0",
            capabilities=ServerCapabilities(
                tools=ToolsCapability()
            )
        )
        
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, initialization_options)
    
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
