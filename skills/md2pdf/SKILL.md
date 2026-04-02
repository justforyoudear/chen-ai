---
name: md2pdf
description: Use when converting markdown files to PDF with Chinese content, Mermaid diagrams, or when ReportLab-based tools produce black boxes or spacing issues for CJK text. Triggers on markdown-to-PDF, Chinese PDF, Mermaid PDF export.
---

# md2pdf — Markdown to PDF via Playwright

## Overview

Convert markdown files to high-quality PDF using Playwright (Chromium). Handles Chinese/CJK text natively via browser font fallback, embeds Mermaid diagrams as rendered PNGs, and produces clean compact layout with no black boxes.

**Key advantage over ReportLab-based tools:** Chromium's font fallback chain renders CJK characters correctly in ALL contexts (headings, code blocks, tables) without font registration hacks.

## When to Use

- Markdown contains Chinese/CJK text and needs PDF output
- Mermaid diagrams in markdown need to be rendered as images in PDF
- ReportLab/minimax-pdf produces black boxes (tofu) for Chinese characters
- Code blocks with Chinese comments or ASCII art need correct rendering

## Quick Reference

```bash
# Basic usage
python scripts/md2pdf.py input.md -o output.pdf

# With custom Mermaid scale and width
python scripts/md2pdf.py input.md -o output.pdf --mermaid-scale 4 --img-width 85

# Specify output directory for temp files (default: same as input)
python scripts/md2pdf.py input.md -o output.pdf --work-dir ./build
```

## Process

```
input.md
  |
  +--> Extract Mermaid blocks --> mmdc --> PNG files
  |
  +--> Convert markdown to HTML (replace Mermaid with <img>)
  |
  +--> Inline CSS (Chinese fonts, compact spacing)
  |
  +--> Playwright chromium --> page.pdf()
  |
  +--> Cleanup temp files (HTML, PNGs, config)
  |
  v
output.pdf
```

## Implementation

The reusable script is at `scripts/md2pdf.py`.

Key design decisions baked into the script:

| Decision | Why |
|----------|-----|
| Playwright instead of ReportLab | Browser font fallback handles CJK natively; no black boxes |
| Mermaid pre-rendered via mmdc | Mermaid.js in-browser rendering is flaky in headless; CLI is reliable |
| `page-break-inside: auto` for code blocks | `avoid` causes large blank gaps at page bottoms |
| Compact margins (3-5px) | Default 10-30px margins create excessive whitespace |
| `Consolas` + browser fallback for code | Consolas for ASCII art, browser auto-falls back to system CJK font |
| Cleanup intermediate files | PNGs and temp HTML can be large; only final PDF is kept |

## CSS Defaults

```css
/* Critical for CJK */
body { font-family: "Microsoft YaHei UI", "Noto Sans SC", "SimHei", sans-serif; }
pre code { font-family: "Consolas", "Source Code Pro", monospace; }
/* Chromium auto-falls back to system CJK font for Chinese in code blocks */

/* Compact spacing (key values) */
h1 { margin-top: 14px; margin-bottom: 4px; }
h2 { margin-top: 10px; margin-bottom: 3px; }
p  { margin: 2px 0; }
pre { margin: 3px 0; page-break-inside: auto; }
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Using ReportLab for CJK content | Use Playwright instead — browser handles font fallback |
| `page-break-inside: avoid` on code blocks | Causes large blank gaps at page bottoms; use `auto` |
| Large heading margins (24-30px) | Use 10-14px max for compact layout |
| Forgetting `print_background: True` | Background colors won't render in PDF |
| Using `.pdf` extension for HTML temp files | Chromium treats it as download, not render; use `.html` |

## Dependencies

- Python 3.10+
- `playwright` (pip install playwright && playwright install chromium)
- `mermaid-cli` (npm install -g @mermaid-js/mermaid-cli)
- System fonts: Microsoft YaHei / Noto Sans SC / SimHei (for Chinese)
