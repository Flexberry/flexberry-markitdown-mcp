"""Tests for the MD→PDF converter module."""

import tempfile
from pathlib import Path

import pytest

from flexberry_markitdown_mcp.converter import (
    build_html_document,
    convert_md_file_to_pdf,
    convert_md_to_pdf,
    markdown_to_html,
)


# ---------------------------------------------------------------------------
# markdown_to_html
# ---------------------------------------------------------------------------

class TestMarkdownToHtml:
    def test_basic_paragraph(self):
        result = markdown_to_html("Hello, world!")
        assert "<p>Hello, world!</p>" in result

    def test_heading(self):
        result = markdown_to_html("# Title")
        assert "<h1>Title</h1>" in result

    def test_table(self):
        md = "| A | B |\n|---|---|\n| 1 | 2 |"
        result = markdown_to_html(md)
        assert "<table>" in result

    def test_tasklist(self):
        md = "- [x] done\n- [ ] todo"
        result = markdown_to_html(md)
        assert "checkbox" in result.lower() or "task" in result.lower()

    def test_strikethrough(self):
        md = "~~deleted~~"
        result = markdown_to_html(md)
        assert "<s>deleted</s>" in result or "<del>deleted</del>" in result

    def test_code_block(self):
        md = "```python\nprint('hi')\n```"
        result = markdown_to_html(md)
        assert "print" in result

    def test_frontmatter_consumed(self):
        md = "---\ntitle: Test\n---\n\nContent here"
        result = markdown_to_html(md)
        assert "Content here" in result
        assert "<h2>title: Test</h2>" not in result

    def test_disable_features(self):
        result = markdown_to_html("~~deleted~~", enable_strikethrough=False)
        assert "<s>" not in result and "<del>" not in result


# ---------------------------------------------------------------------------
# build_html_document
# ---------------------------------------------------------------------------

class TestBuildHtmlDocument:
    def test_basic(self):
        html = build_html_document("<p>Hello</p>", title="Test")
        assert "<!DOCTYPE html>" in html
        assert "<title>Test</title>" in html
        assert "<p>Hello</p>" in html

    def test_no_default_styles(self):
        html = build_html_document("<p>Hello</p>", include_default_styles=False)
        assert len(html) < 500

    def test_custom_css(self):
        html = build_html_document("<p>Hello</p>", custom_css="body { color: red; }")
        assert "body { color: red; }" in html


# ---------------------------------------------------------------------------
# convert_md_to_pdf (WeasyPrint — used in CI without browser)
# ---------------------------------------------------------------------------

class TestConvertMdToPdfWeasyprint:
    def test_basic_pdf_generation(self, tmp_path):
        md_text = "# Hello, PDF!\n\nThis is a test document."
        output = tmp_path / "test.pdf"
        convert_md_to_pdf(md_text, output, backend="weasyprint")
        assert output.exists()
        assert output.stat().st_size > 0

    def test_pdf_with_table(self, tmp_path):
        md_text = "# Table Test\n\n| A | B |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |"
        output = tmp_path / "table.pdf"
        convert_md_to_pdf(md_text, output, backend="weasyprint")
        assert output.exists()
        assert output.stat().st_size > 0

    def test_pdf_with_code_block(self, tmp_path):
        md_text = "# Code\n\n```python\ndef hello():\n    print('Hello!')\n```"
        output = tmp_path / "code.pdf"
        convert_md_to_pdf(md_text, output, backend="weasyprint")
        assert output.exists()

    def test_invalid_backend_raises(self, tmp_path):
        with pytest.raises(ValueError, match="Unknown PDF backend"):
            convert_md_to_pdf("# Test", tmp_path / "out.pdf", backend="nonexistent")

    def test_cyrillic_content(self, tmp_path):
        md_text = "# Привет, мир!\n\nЭто тестовый документ на русском языке."
        output = tmp_path / "cyrillic.pdf"
        convert_md_to_pdf(md_text, output, backend="weasyprint")
        assert output.exists()
        assert output.stat().st_size > 0

    def test_default_backend_is_playwright(self):
        """Verify that the default backend argument is 'playwright'."""
        import inspect
        sig = inspect.signature(convert_md_to_pdf)
        assert sig.parameters["backend"].default == "playwright"


# ---------------------------------------------------------------------------
# convert_md_file_to_pdf
# ---------------------------------------------------------------------------

class TestConvertMdFileToPdf:
    def test_from_file(self, tmp_path):
        md_file = tmp_path / "doc.md"
        md_file.write_text("# File Test\n\nFrom a file.", encoding="utf-8")
        output = tmp_path / "doc.pdf"
        convert_md_file_to_pdf(md_file, output, backend="weasyprint")
        assert output.exists()

    def test_auto_output_path(self, tmp_path):
        md_file = tmp_path / "auto.md"
        md_file.write_text("# Auto Path\n\nTest.", encoding="utf-8")
        result = convert_md_file_to_pdf(md_file, backend="weasyprint")
        assert result.exists()
        assert result.suffix == ".pdf"
        assert result.stem == "auto"

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            convert_md_file_to_pdf(tmp_path / "nonexistent.md")

    def test_default_backend_is_playwright(self):
        """Verify that the default backend argument is 'playwright'."""
        import inspect
        sig = inspect.signature(convert_md_file_to_pdf)
        assert sig.parameters["backend"].default == "playwright"
