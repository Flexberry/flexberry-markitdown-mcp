"""Default CSS styles for PDF export, inspired by vscode-markdown-pdf."""


def get_pygments_css() -> str:
    """
    Generate syntax highlighting CSS from Pygments.

    Uses Pygments' built-in HtmlFormatter to produce CSS that matches
    the actual class names generated during code highlighting. Falls back
    to an empty string if Pygments is not installed.

    The result is cached after the first call.
    """
    try:
        from pygments.formatters import HtmlFormatter

        formatter = HtmlFormatter(cssclass="highlight")
        return (
            "/* Syntax highlighting (auto-generated from Pygments) */\n"
            + formatter.get_style_defs(".highlight")
        )
    except ImportError:
        return ""

DEFAULT_PDF_STYLES = """
/* ===== Base Typography ===== */
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial,
                 sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
    font-size: 14px;
    line-height: 1.6;
    color: #24292e;
    max-width: 980px;
    margin: 0 auto;
    padding: 45px;
}

/* ===== Headings ===== */
h1, h2, h3, h4, h5, h6 {
    margin-top: 24px;
    margin-bottom: 16px;
    font-weight: 600;
    line-height: 1.25;
}

h1 {
    font-size: 2em;
    padding-bottom: 0.3em;
    border-bottom: 1px solid #eaecef;
}

h2 {
    font-size: 1.5em;
    padding-bottom: 0.3em;
    border-bottom: 1px solid #eaecef;
}

h3 { font-size: 1.25em; }
h4 { font-size: 1em; }
h5 { font-size: 0.875em; }
h6 { font-size: 0.85em; color: #6a737d; }

/* ===== Paragraphs ===== */
p {
    margin-top: 0;
    margin-bottom: 16px;
}

/* ===== Links ===== */
a {
    color: #0366d6;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

/* ===== Lists ===== */
ul, ol {
    padding-left: 2em;
    margin-top: 0;
    margin-bottom: 16px;
}

li {
    margin-bottom: 0.25em;
}

li > p {
    margin-top: 16px;
}

li + li {
    margin-top: 0.25em;
}

/* ===== Code ===== */
code {
    padding: 0.2em 0.4em;
    margin: 0;
    font-size: 85%;
    background-color: rgba(27, 31, 35, 0.05);
    border-radius: 3px;
    font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
}

pre {
    padding: 16px;
    overflow: auto;
    font-size: 85%;
    line-height: 1.45;
    background-color: #f6f8fa;
    border-radius: 6px;
    margin-top: 0;
    margin-bottom: 16px;
}

pre code {
    display: inline;
    max-width: auto;
    padding: 0;
    margin: 0;
    overflow: visible;
    line-height: inherit;
    word-wrap: normal;
    background-color: transparent;
    border: 0;
}

/* ===== Blockquotes ===== */
blockquote {
    padding: 0 1em;
    color: #6a737d;
    border-left: 0.25em solid #dfe2e5;
    margin: 0 0 16px 0;
}

blockquote > :first-child {
    margin-top: 0;
}

blockquote > :last-child {
    margin-bottom: 0;
}

/* ===== Tables ===== */
table {
    border-spacing: 0;
    border-collapse: collapse;
    margin-top: 0;
    margin-bottom: 16px;
    width: 100%;
    overflow: auto;
}

table th,
table td {
    padding: 6px 13px;
    border: 1px solid #dfe2e5;
}

table th {
    font-weight: 600;
    background-color: #f6f8fa;
}

table tr {
    background-color: #fff;
    border-top: 1px solid #c6cbd1;
}

table tr:nth-child(2n) {
    background-color: #f6f8fa;
}

/* ===== Horizontal Rule ===== */
hr {
    height: 0.25em;
    padding: 0;
    margin: 24px 0;
    background-color: #e1e4e8;
    border: 0;
}

/* ===== Images ===== */
img {
    max-width: 100%;
    box-sizing: content-box;
    background-color: #fff;
}

/* ===== Task Lists (checkboxes) ===== */
.task-list-item {
    list-style-type: none;
}

.task-list-item input[type="checkbox"] {
    margin: 0 0.35em 0.25em -1.6em;
    vertical-align: middle;
}

/* ===== Page Breaks ===== */
.page-break {
    page-break-after: always;
}

/* ===== Math / KaTeX ===== */
.katex-display {
    margin: 1em 0;
    overflow-x: auto;
    overflow-y: hidden;
}

.katex {
    font-size: 1.1em;
}

/* ===== Print-specific ===== */
@page {
    size: A4;
    margin: 1.5cm 1cm 1cm 1cm;
}

@media print {
    body {
        padding: 0;
        max-width: none;
    }

    h1, h2, h3, h4, h5, h6 {
        page-break-after: avoid;
        page-break-inside: avoid;
    }

    table, figure, pre, blockquote {
        page-break-inside: avoid;
    }

    img {
        page-break-inside: avoid;
    }

    tr, td, th {
        page-break-inside: avoid;
    }
}
"""
