"""Tests for server module functions."""

import asyncio
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from mcp.types import TextContent

# Mock stdin before importing server module
sys.stdin = MagicMock()
sys.stdin.reconfigure = MagicMock()

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestUtilityFunctions:
    """Tests for utility functions in server.py."""

    def test_dump_codepoints(self):
        """Test dump_codepoints function."""
        from flexberry_markitdown_mcp.server import dump_codepoints

        # Test ASCII
        assert dump_codepoints("abc") == "U+0061 U+0062 U+0063"

        # Test Cyrillic
        assert dump_codepoints("Кейс") == "U+041A U+0435 U+0439 U+0441"

    def test_get_supported_extensions_description(self):
        """Test get_supported_extensions_description function."""
        from flexberry_markitdown_mcp.server import get_supported_extensions_description

        desc = get_supported_extensions_description()
        assert "PDF" in desc
        assert "DOCX" in desc
        assert "PNG" in desc
        assert "MP3" in desc


class TestPathFunctions:
    """Tests for path handling functions."""

    def test_normalize_path_with_tilde(self):
        """Test normalize_path expands user home directory."""
        from flexberry_markitdown_mcp.server import normalize_path

        # This will expand ~ to home directory
        result = normalize_path("~/test.txt")
        assert result.is_absolute()

    def test_normalize_path_absolute(self):
        """Test normalize_path returns absolute path."""
        from flexberry_markitdown_mcp.server import normalize_path

        result = normalize_path("/tmp/test.txt")
        assert result.is_absolute()

    def test_generate_output_path(self):
        """Test generate_output_path function."""
        from flexberry_markitdown_mcp.server import generate_output_path

        input_path = Path("/tmp/document.docx")
        output_path = generate_output_path(input_path)
        assert output_path == Path("/tmp/document.md")

    def test_generate_output_path_with_special_chars(self):
        """Test generate_output_path with Cyrillic filename."""
        from flexberry_markitdown_mcp.server import generate_output_path

        input_path = Path("/tmp/документ.docx")
        output_path = generate_output_path(input_path)
        assert output_path.suffix == ".md"

    def test_make_unique_path(self):
        """Test make_unique_path function."""
        from flexberry_markitdown_mcp.server import make_unique_path

        with tempfile.TemporaryDirectory() as tmpdir:
            # Test with non-existing file
            path = Path(tmpdir) / "test.txt"
            result = make_unique_path(path)
            assert result == path

            # Create the file
            path.write_text("test")

            # Test with existing file
            result = make_unique_path(path)
            assert "(1)" in result.name

            # Create the (1) file
            result.write_text("test")

            # Test with existing (1) file
            result2 = make_unique_path(path)
            assert "(2)" in result2.name


class TestResolveExistingFile:
    """Tests for resolve_existing_file function."""

    def test_resolve_existing_file_direct(self):
        """Test resolve_existing_file with direct path."""
        from flexberry_markitdown_mcp.server import resolve_existing_file

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("content")

            result = resolve_existing_file(str(test_file))
            assert result == test_file

    def test_resolve_existing_file_not_found(self):
        """Test resolve_existing_file raises FileNotFoundError."""
        from flexberry_markitdown_mcp.server import resolve_existing_file

        with pytest.raises(FileNotFoundError):
            resolve_existing_file("/nonexistent/path/file.txt")

    def test_resolve_existing_file_unicode_normalization(self):
        """Test resolve_existing_file handles Unicode normalization."""
        from flexberry_markitdown_mcp.server import resolve_existing_file

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create file with NFC normalization
            test_file = Path(tmpdir) / "тест.txt"
            test_file.write_text("content")

            # Try to resolve with NFD normalization
            import unicodedata

            nfd_name = unicodedata.normalize("NFD", test_file.name)
            nfd_path = test_file.parent / nfd_name

            result = resolve_existing_file(str(nfd_path))
            assert result.exists()


class TestServerTools:
    """Tests for server tool handlers."""

    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test list_tools returns expected tools."""
        from flexberry_markitdown_mcp.server import list_tools

        tools = await list_tools()
        tool_names = [tool.name for tool in tools]

        assert "convert_to_markdown" in tool_names
        assert "get_supported_formats" in tool_names
        assert "check_file_exists" in tool_names
        assert "list_directory" in tool_names

    @pytest.mark.asyncio
    async def test_call_tool_get_supported_formats(self):
        """Test call_tool for get_supported_formats."""
        from flexberry_markitdown_mcp.server import call_tool

        result = await call_tool("get_supported_formats", {})
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "PDF" in result[0].text

    @pytest.mark.asyncio
    async def test_call_tool_unknown_tool(self):
        """Test call_tool with unknown tool name."""
        from flexberry_markitdown_mcp.server import call_tool

        result = await call_tool("unknown_tool", {})
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "Unknown tool" in result[0].text

    @pytest.mark.asyncio
    async def test_call_tool_list_directory(self):
        """Test call_tool for list_directory."""
        from flexberry_markitdown_mcp.server import call_tool

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            (Path(tmpdir) / "test.txt").write_text("content")
            (Path(tmpdir) / "test.docx").write_text("content")

            result = await call_tool("list_directory", {"directory_path": tmpdir})
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], TextContent)
            assert "test.txt" in result[0].text
            assert "test.docx" in result[0].text

    @pytest.mark.asyncio
    async def test_call_tool_check_file_exists(self):
        """Test call_tool for check_file_exists."""
        from flexberry_markitdown_mcp.server import call_tool

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("content")

            result = await call_tool("check_file_exists", {"file_path": str(test_file)})
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], TextContent)
            assert "test.txt" in result[0].text
            assert "Yes" in result[0].text  # Supported format

    @pytest.mark.asyncio
    async def test_call_tool_check_file_not_exists(self):
        """Test call_tool for check_file_exists with non-existent file."""
        from flexberry_markitdown_mcp.server import call_tool

        result = await call_tool("check_file_exists", {"file_path": "/nonexistent/file.txt"})
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "does not exist" in result[0].text or "File does not exist" in result[0].text

    @pytest.mark.asyncio
    async def test_call_tool_convert_to_markdown(self):
        """Test call_tool for convert_to_markdown."""
        from flexberry_markitdown_mcp.server import call_tool

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple text file
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("Hello, World!")

            result = await call_tool("convert_to_markdown", {"file_path": str(test_file)})
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], TextContent)
            assert "Conversion successful" in result[0].text

            # Check output file was created
            output_file = Path(tmpdir) / "test.md"
            assert output_file.exists()
            assert "Hello, World!" in output_file.read_text()

    @pytest.mark.asyncio
    async def test_call_tool_convert_to_markdown_unsupported_format(self):
        """Test call_tool for convert_to_markdown with unsupported format."""
        from flexberry_markitdown_mcp.server import call_tool

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file with unsupported extension
            test_file = Path(tmpdir) / "test.xyz"
            test_file.write_text("content")

            result = await call_tool("convert_to_markdown", {"file_path": str(test_file)})
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], TextContent)
            assert "Error" in result[0].text or "Unsupported" in result[0].text

    @pytest.mark.asyncio
    async def test_call_tool_convert_to_markdown_missing_file(self):
        """Test call_tool for convert_to_markdown with missing file."""
        from flexberry_markitdown_mcp.server import call_tool

        result = await call_tool("convert_to_markdown", {"file_path": "/nonexistent/file.txt"})
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "Error" in result[0].text or "does not exist" in result[0].text

    @pytest.mark.asyncio
    async def test_call_tool_convert_to_markdown_missing_file_path(self):
        """Test call_tool for convert_to_markdown without file_path."""
        from flexberry_markitdown_mcp.server import call_tool

        result = await call_tool("convert_to_markdown", {})
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "Error" in result[0].text
        assert "file_path" in result[0].text

    @pytest.mark.asyncio
    async def test_call_tool_list_directory_missing_path(self):
        """Test call_tool for list_directory without directory_path."""
        from flexberry_markitdown_mcp.server import call_tool

        result = await call_tool("list_directory", {})
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        # Should list current directory

    @pytest.mark.asyncio
    async def test_call_tool_check_file_exists_missing_path(self):
        """Test call_tool for check_file_exists without file_path."""
        from flexberry_markitdown_mcp.server import call_tool

        result = await call_tool("check_file_exists", {})
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "Error" in result[0].text
