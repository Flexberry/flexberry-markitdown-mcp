"""
Markdown-to-PDF conversion module.

Default backend: Playwright (headless Chromium) — same approach as vscode-markdown-pdf
which uses puppeteer-core. Chromium is auto-downloaded on first use.

Optional backend: WeasyPrint — pure-Python, no browser required (no JS rendering).

Pipeline: MD → HTML (via markdown-it-py) → full HTML doc → PDF
"""

from __future__ import annotations

import logging
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from markdown_it import MarkdownIt

from .styles import DEFAULT_PDF_STYLES, get_pygments_css

logger = logging.getLogger(__name__)

# Track whether we've already ensured Chromium is installed
_chromium_ensured = False


# ---------------------------------------------------------------------------
# Chromium auto-install (mirrors vscode-markdown-pdf behavior)
# ---------------------------------------------------------------------------


def ensure_chromium() -> None:
    """
    Ensure Chromium browser is installed for Playwright.

    This mirrors the vscode-markdown-pdf approach:
    on first PDF generation, automatically download Chromium if not present.
    After `pip install flexberry-markitdown-mcp`, the user does NOT need
    to manually run `playwright install chromium` — it happens automatically.
    """
    global _chromium_ensured
    if _chromium_ensured:
        return

    try:
        from playwright.sync_api import sync_playwright

        # Check if the Chromium executable exists without launching a browser.
        # Playwright computes the expected path from its internal registry;
        # if the file is missing the browser needs to be installed.
        with sync_playwright() as pw:
            exec_path = pw.chromium.executable_path
            if exec_path and Path(exec_path).exists():
                logger.info("Chromium browser is available")
            else:
                logger.info("Chromium not found, auto-installing (one-time setup)...")
                _install_chromium()

    except ImportError as err:
        raise ImportError(
            "playwright is required for PDF generation. Install with: pip install flexberry-markitdown-mcp"
        ) from err

    _chromium_ensured = True


def _install_chromium() -> None:
    """Run `playwright install chromium` to download the browser."""
    logger.info("Running: playwright install chromium ...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            capture_output=True,
            text=True,
            timeout=300,  # 5 min timeout for download
        )
        if result.returncode != 0:
            logger.error(f"playwright install chromium failed:\n{result.stderr}")
            raise RuntimeError(
                f"Failed to auto-install Chromium.\n"
                f"stdout: {result.stdout}\nstderr: {result.stderr}\n"
                f"Try manually: playwright install chromium"
            )
        logger.info("Chromium installed successfully")
    except subprocess.TimeoutExpired as err:
        raise RuntimeError("Chromium download timed out (5 min). Try manually: playwright install chromium") from err


# ---------------------------------------------------------------------------
# Markdown → HTML
# ---------------------------------------------------------------------------


def markdown_to_html(
    md_text: str,
    enable_table: bool = True,
    enable_strikethrough: bool = True,
    enable_tasklists: bool = True,
    enable_frontmatter: bool = True,
) -> str:
    """
    Convert Markdown text to HTML using markdown-it-py with common plugins.

    Supported features (enabled by default):
      - table:         GFM tables (built-in rule)
      - strikethrough: ~~deleted~~ (built-in rule)
      - tasklists:     - [x] / - [ ] checkboxes (mdit-py-plugins)
      - frontmatter:   YAML front matter (consumed, not rendered) (mdit-py-plugins)

    Args:
        md_text:              Raw Markdown content.
        enable_table:         Enable GFM table support.
        enable_strikethrough: Enable ~~strikethrough~~ support.
        enable_tasklists:     Enable GitHub-style task lists.
        enable_frontmatter:   Enable YAML front matter parsing.

    Returns:
        HTML string (body content only, no <html>/<head> wrapper).
    """
    try:
        from markdown_it import MarkdownIt
    except ImportError as err:
        raise ImportError(
            "markdown-it-py is required for MD→PDF conversion. Install it with: pip install markdown-it-py"
        ) from err

    # Start with commonmark preset and enable GFM extras (built-in rules)
    built_in_rules = []
    if enable_table:
        built_in_rules.append("table")
    if enable_strikethrough:
        built_in_rules.append("strikethrough")

    md = MarkdownIt("commonmark", {"html": True}).enable(built_in_rules)

    # Load external plugins (mdit-py-plugins)
    if enable_tasklists:
        try:
            from mdit_py_plugins.tasklists import tasklists_plugin

            md.use(tasklists_plugin)
        except ImportError:
            logger.debug("mdit-py-plugins not installed, task lists disabled")

    if enable_frontmatter:
        try:
            from mdit_py_plugins.front_matter import front_matter_plugin

            md.use(front_matter_plugin)
        except ImportError:
            logger.debug("mdit-py-plugins not installed, front matter disabled")

    # Pygments-based syntax highlighting for fenced code blocks
    try:
        md = _enable_highlighting(md)
    except Exception:
        logger.debug("Syntax highlighting not available, using plain code blocks")

    html_body = md.render(md_text)
    return html_body


def _enable_highlighting(md: MarkdownIt) -> MarkdownIt:
    """Add Pygments-based syntax highlighting to the markdown-it instance."""
    try:
        from pygments import highlight
        from pygments.formatters import HtmlFormatter
        from pygments.lexers import ClassNotFound, get_lexer_by_name, guess_lexer

        def highlight_code(code: str, lang: str, *args) -> str:
            if lang:
                try:
                    lexer = get_lexer_by_name(lang, stripall=True)
                except ClassNotFound:
                    lexer = guess_lexer(code)
            else:
                lexer = guess_lexer(code)
            formatter = HtmlFormatter(cssclass="highlight", nowrap=False)
            return highlight(code, lexer, formatter)

        md.options["highlight"] = highlight_code
    except ImportError:
        logger.debug("Pygments not installed, skipping syntax highlighting")
    return md


# ---------------------------------------------------------------------------
# HTML → full document
# ---------------------------------------------------------------------------

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>{title}</title>
<style>
{styles}
</style>
</head>
<body>
{content}
</body>
</html>
"""


def build_html_document(
    html_body: str,
    title: str = "Document",
    lang: str = "en",
    custom_css: str = "",
    include_default_styles: bool = True,
) -> str:
    """
    Wrap rendered HTML body in a full HTML document with styles.

    Args:
        html_body:               Inner HTML content.
        title:                   Document <title>.
        lang:                    HTML lang attribute.
        custom_css:              Additional CSS to append.
        include_default_styles:  Whether to include the built-in stylesheet.

    Returns:
        Complete HTML document string.
    """
    styles = ""
    if include_default_styles:
        styles = DEFAULT_PDF_STYLES + "\n" + get_pygments_css()
    if custom_css:
        styles += "\n" + custom_css

    return HTML_TEMPLATE.format(
        lang=lang,
        title=title,
        styles=styles,
        content=html_body,
    )


# ---------------------------------------------------------------------------
# HTML → PDF  (Playwright backend — DEFAULT)
# ---------------------------------------------------------------------------


def html_to_pdf_playwright(
    html: str,
    output_path: Path,
    format: str = "A4",
    margin_top: str = "1.5cm",
    margin_bottom: str = "1cm",
    margin_left: str = "1cm",
    margin_right: str = "1cm",
    print_background: bool = True,
    display_header_footer: bool = True,
    header_template: str = "",
    footer_template: str = "",
) -> Path:
    """
    Convert HTML string to PDF using Playwright (headless Chromium).

    This is the default backend, matching vscode-markdown-pdf which uses
    puppeteer-core + headless Chrome. It supports JavaScript-rendered content
    (Mermaid diagrams, PlantUML, etc.) because it uses a real browser engine.

    Chromium is auto-downloaded on first use (see ensure_chromium()).

    Args:
        html:                  Full HTML document string.
        output_path:           Where to save the PDF.
        format:                Paper format (A4, Letter, etc.).
        margin_top/bottom/left/right: Page margins.
        print_background:      Whether to print background colors/images.
        display_header_footer: Whether to show header/footer.
        header_template:       HTML template for the header.
        footer_template:       HTML template for the footer.

    Returns:
        Path to the generated PDF file.
    """
    from playwright.sync_api import sync_playwright  # type: ignore[import-untyped]

    # Ensure Chromium is available (auto-download on first use)
    ensure_chromium()

    # Write HTML to temp file so that file:// URLs work correctly
    # (same approach as vscode-markdown-pdf: write tmp HTML, load via file://)
    with tempfile.NamedTemporaryFile(suffix=".html", mode="w", encoding="utf-8", delete=False) as tmp:
        tmp.write(html)
        tmp_path = Path(tmp.name)

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            # vscode-markdown-pdf uses networkidle0 — Playwright equivalent is "networkidle"
            page.goto(f"file://{tmp_path}", wait_until="networkidle")
            page.pdf(
                path=str(output_path),
                format=format,
                margin={
                    "top": margin_top,
                    "bottom": margin_bottom,
                    "left": margin_left,
                    "right": margin_right,
                },
                print_background=print_background,
                display_header_footer=display_header_footer,
                header_template=header_template,
                footer_template=footer_template,
            )
            browser.close()
    finally:
        tmp_path.unlink(missing_ok=True)

    return output_path


# ---------------------------------------------------------------------------
# HTML → PDF  (WeasyPrint backend — OPTIONAL)
# ---------------------------------------------------------------------------


def html_to_pdf_weasyprint(
    html: str,
    output_path: Path,
) -> Path:
    """
    Convert HTML string to PDF using WeasyPrint (pure Python, no browser).

    This is an optional lightweight backend. It does NOT support JavaScript-
    rendered content (Mermaid, PlantUML), but requires no browser installation.

    Install with: pip install flexberry-markitdown-mcp[weasyprint]

    Args:
        html:        Full HTML document string.
        output_path: Where to save the PDF.

    Returns:
        Path to the generated PDF file.
    """
    try:
        from weasyprint import HTML
    except ImportError as err:
        raise ImportError(
            "weasyprint is not installed. Install with: pip install flexberry-markitdown-mcp[weasyprint]"
        ) from err

    with tempfile.NamedTemporaryFile(suffix=".html", mode="w", encoding="utf-8", delete=False) as tmp:
        tmp.write(html)
        tmp_path = Path(tmp.name)

    try:
        doc = HTML(filename=str(tmp_path), base_url=str(output_path.parent))
        doc.write_pdf(str(output_path))
    finally:
        tmp_path.unlink(missing_ok=True)

    return output_path


# ---------------------------------------------------------------------------
# High-level: MD → PDF
# ---------------------------------------------------------------------------

# Default footer with page numbers (matching vscode-markdown-pdf style)
DEFAULT_FOOTER_TEMPLATE = (
    '<div style="font-size: 9px; margin: 0 auto; width: 100%; text-align: center;">'
    '<span class="pageNumber"></span> / <span class="totalPages"></span>'
    "</div>"
)

DEFAULT_HEADER_TEMPLATE = (
    '<div style="font-size: 9px; margin-left: 1cm; width: 100%;"><span class="title"></span></div>'
)


def convert_md_to_pdf(
    md_text: str,
    output_path: Path,
    title: str = "Document",
    lang: str = "en",
    custom_css: str = "",
    include_default_styles: bool = True,
    backend: str = "playwright",
    # Page options (used by Playwright; WeasyPrint uses CSS @page)
    format: str = "A4",
    margin_top: str = "1.5cm",
    margin_bottom: str = "1cm",
    margin_left: str = "1cm",
    margin_right: str = "1cm",
    print_background: bool = True,
    display_header_footer: bool = True,
    header_template: str = "",
    footer_template: str = "",
) -> Path:
    """
    Convert Markdown text to PDF.

    This is the main entry point that orchestrates the full pipeline:
      1. MD → HTML  (markdown-it-py)
      2. HTML → full document  (template + styles)
      3. HTML → PDF  (playwright by default, or weasyprint)

    Default backend is playwright (headless Chromium), matching vscode-markdown-pdf.
    Chromium is auto-downloaded on first use.

    Args:
        md_text:                Raw Markdown content.
        output_path:            Where to save the PDF.
        title:                  Document title.
        lang:                   Document language.
        custom_css:             Additional CSS to inject.
        include_default_styles: Whether to include built-in GitHub-like styles.
        backend:                "playwright" (default) or "weasyprint".
        format:                 Paper format: A4, Letter, etc.
        margin_top/bottom/left/right: Page margins.
        print_background:       Print background colors/images.
        display_header_footer:  Show header/footer (playwright only).
        header_template:        Header HTML (playwright only).
        footer_template:        Footer HTML (playwright only).

    Returns:
        Path to the generated PDF file.
    """
    logger.info(f"Converting MD to PDF: backend={backend}, output={output_path}")

    # Step 1: MD → HTML body
    html_body = markdown_to_html(md_text)
    logger.debug(f"Markdown rendered to {len(html_body)} chars of HTML")

    # Step 2: Build full HTML document
    html_doc = build_html_document(
        html_body=html_body,
        title=title,
        lang=lang,
        custom_css=custom_css,
        include_default_styles=include_default_styles,
    )

    # Step 3: HTML → PDF
    if backend == "playwright":
        if not header_template:
            header_template = DEFAULT_HEADER_TEMPLATE
        if not footer_template:
            footer_template = DEFAULT_FOOTER_TEMPLATE
        html_to_pdf_playwright(
            html=html_doc,
            output_path=output_path,
            format=format,
            margin_top=margin_top,
            margin_bottom=margin_bottom,
            margin_left=margin_left,
            margin_right=margin_right,
            print_background=print_background,
            display_header_footer=display_header_footer,
            header_template=header_template,
            footer_template=footer_template,
        )
    elif backend == "weasyprint":
        html_to_pdf_weasyprint(
            html=html_doc,
            output_path=output_path,
        )
    else:
        raise ValueError(f"Unknown PDF backend: {backend!r}. Supported backends: 'playwright' (default), 'weasyprint'")

    logger.info(f"PDF generated: {output_path} ({output_path.stat().st_size:,} bytes)")
    return output_path


def convert_md_file_to_pdf(
    input_path: Path,
    output_path: Path | None = None,
    backend: str = "playwright",
    **kwargs,
) -> Path:
    """
    Convert a Markdown file to PDF.

    Args:
        input_path:  Path to the .md file.
        output_path: Where to save the PDF. Defaults to same directory, .pdf extension.
        backend:     PDF backend ("playwright" default, or "weasyprint").
        **kwargs:    Additional arguments passed to convert_md_to_pdf().

    Returns:
        Path to the generated PDF file.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    md_text = input_path.read_text(encoding="utf-8")

    if output_path is None:
        output_path = input_path.with_suffix(".pdf")

    title = kwargs.pop("title", input_path.stem)

    return convert_md_to_pdf(
        md_text=md_text,
        output_path=output_path,
        title=title,
        backend=backend,
        **kwargs,
    )
