#!/usr/bin/env python3
"""
md2pdf.py — Convert markdown to PDF via Playwright.

Handles:
  - Chinese/CJK text (browser font fallback, no tofu)
  - Mermaid diagrams (pre-rendered to PNG via mmdc)
  - Compact layout, no cover page
  - Cleanup of intermediate files

Usage:
  python md2pdf.py input.md -o output.pdf
  python md2pdf.py input.md -o output.pdf --mermaid-scale 4 --img-width 85
  python md2pdf.py input.md -o output.pdf --work-dir ./build
"""

import argparse, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path


# ─── Markdown → HTML ────────────────────────────────────────────────

def escape_html(text):
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))


def convert_inline(text):
    """Process inline markdown: code, bold, italic, links."""
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    return text


def convert_table(lines):
    """Convert markdown table rows to HTML table."""
    data_lines = [l for l in lines
                  if not re.match(r'^\s*\|?[\s\-:]+\|[\s\-:|]+\|?\s*$', l)]
    if not data_lines:
        return ""
    html = "<table>\n"
    for i, line in enumerate(data_lines):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        tag = "th" if i == 0 else "td"
        html += "  <tr>" + "".join(f"<{tag}>{convert_inline(c)}</{tag}>" for c in cells) + "</tr>\n"
    html += "</table>\n"
    return html


def md_to_html(md_text, mermaid_images=None):
    """
    Convert markdown to HTML body.
    mermaid_images: list of file paths/URIs for pre-rendered Mermaid PNGs.
    """
    if mermaid_images is None:
        mermaid_images = []

    lines = md_text.split("\n")
    parts = []
    mermaid_idx = 0
    in_code = False
    code_lines = []
    code_lang = ""
    list_stack = []  # [(tag, indent_level)]

    def close_lists_to(level):
        while list_stack and list_stack[-1][1] >= level:
            t, _ = list_stack.pop()
            parts.append(f"</{t}>")

    def close_all():
        close_lists_to(-1)

    i = 0
    while i < len(lines):
        raw = lines[i].rstrip()
        bt3 = "`" * 3

        # Code block fence
        if raw.startswith(bt3):
            if not in_code:
                in_code = True
                code_lang = raw[3:].strip()
                code_lines = []
                i += 1
                continue
            else:
                in_code = False
                if code_lang == "mermaid":
                    if mermaid_idx < len(mermaid_images):
                        img_src = mermaid_images[mermaid_idx]
                        if not img_src.startswith("file://"):
                            img_src = Path(img_src).as_uri()
                        parts.append(
                            f'<div class="mermaid-img">'
                            f'<img src="{img_src}" alt="Diagram {mermaid_idx+1}" />'
                            f'</div>\n'
                        )
                        mermaid_idx += 1
                    else:
                        parts.append("<p><em>[Mermaid diagram placeholder]</em></p>\n")
                else:
                    escaped = escape_html("\n".join(code_lines))
                    parts.append(f'<pre><code class="code-block">{escaped}</code></pre>\n')
                code_lines = []
                code_lang = ""
                i += 1
                continue

        if in_code:
            code_lines.append(raw)
            i += 1
            continue

        # Blank line
        if raw.strip() == "":
            close_all()
            i += 1
            continue

        # Table
        if "|" in raw and i + 1 < len(lines):
            if re.match(r"^\s*\|?[\s\-:]+\|[\s\-:|]+\|?\s*$", lines[i + 1]):
                close_all()
                tbl = [raw]
                j = i + 1
                while j < len(lines) and "|" in lines[j]:
                    tbl.append(lines[j])
                    j += 1
                parts.append(convert_table(tbl))
                i = j
                continue

        # Heading
        hm = re.match(r"^(#{1,6})\s+(.+)$", raw)
        if hm:
            close_all()
            level = len(hm.group(1))
            text = convert_inline(hm.group(2).strip())
            parts.append(f"<h{level}>{text}</h{level}>\n")
            i += 1
            continue

        # Bullet list
        lm = re.match(r"^(\s*)[-*]\s+(.+)$", raw)
        if lm:
            indent = len(lm.group(1))
            content = convert_inline(lm.group(2).strip())
            level = indent // 2
            close_lists_to(level)
            if not list_stack or list_stack[-1][1] < level:
                list_stack.append(("ul", level))
                parts.append("<ul>\n")
            parts.append(f"  <li>{content}</li>\n")
            i += 1
            continue

        # Numbered list
        nm = re.match(r"^(\s*\d+)\.\s+(.+)$", raw)
        if nm:
            content = convert_inline(nm.group(2).strip())
            if not list_stack or list_stack[-1][0] != "ol":
                close_all()
                list_stack.append(("ol", 0))
                parts.append("<ol>\n")
            parts.append(f"  <li>{content}</li>\n")
            i += 1
            continue

        # Paragraph
        close_all()
        parts.append(f"<p>{convert_inline(raw)}</p>\n")
        i += 1

    close_all()
    return "".join(parts)


# ─── CSS ─────────────────────────────────────────────────────────────

def build_css(img_width=85):
    return f"""
@page {{ size: A4; margin: 20mm 18mm 25mm 18mm; }}
* {{ box-sizing: border-box; }}
body {{
    font-family: "Microsoft YaHei UI", "Noto Sans SC", "SimHei", "PingFang SC", sans-serif;
    font-size: 11pt; line-height: 1.6; color: #1a1a1a; margin: 0; padding: 0;
}}
h1 {{ font-size: 22pt; color: #1B2A38; border-bottom: 2px solid #1B2A38;
     padding-bottom: 4px; margin-top: 14px; margin-bottom: 4px; }}
h2 {{ font-size: 16pt; color: #2c3e50; border-bottom: 1px solid #dce6f0;
     padding-bottom: 3px; margin-top: 10px; margin-bottom: 3px; }}
h3 {{ font-size: 13pt; color: #34495e; margin-top: 8px; margin-bottom: 3px; }}
h4, h5, h6 {{ font-size: 11pt; color: #555; margin-top: 6px; margin-bottom: 2px; }}
p {{ margin: 2px 0; text-align: justify; }}
pre {{
    background-color: #f5f7f9; border-left: 4px solid #4a90d9; border-radius: 3px;
    padding: 6px 10px; margin: 3px 0; overflow-x: auto;
    page-break-inside: auto; white-space: pre-wrap; word-wrap: break-word;
}}
pre code.code-block {{
    font-family: "Consolas", "Source Code Pro", "Courier New", monospace;
    font-size: 8.5pt; line-height: 1.4; color: #2c3e50; display: block;
}}
code {{
    font-family: "Consolas", "Source Code Pro", monospace; font-size: 9.5pt;
    background-color: #eef2f7; padding: 1px 4px; border-radius: 3px; color: #c0392b;
}}
pre code {{ background: none; padding: 0; color: #2c3e50; }}
table {{ width: 100%; border-collapse: collapse; margin: 4px 0;
         font-size: 10pt; page-break-inside: avoid; }}
th {{ background-color: #1B2A38; color: #fff; font-weight: 600;
     padding: 6px 8px; text-align: left; border: 1px solid #1B2A38; }}
td {{ padding: 4px 8px; border: 1px solid #dce6f0; vertical-align: top; }}
tr:nth-child(even) td {{ background-color: #f8fafc; }}
.mermaid-img {{ text-align: center; margin: 6px 0; page-break-inside: avoid; }}
.mermaid-img img {{ width: {img_width}%; max-width: 100%; height: auto; }}
ul, ol {{ margin: 2px 0 2px 16px; padding: 0; }}
li {{ margin: 1px 0; }}
a {{ color: #2980b9; text-decoration: none; }}
"""


# ─── Mermaid → PNG ───────────────────────────────────────────────────

def render_mermaid(md_text, work_dir, scale=4, width=2000):
    """Extract Mermaid blocks and render to PNG via mmdc."""
    blocks = re.findall(r'```mermaid\s*\n(.*?)```', md_text, re.DOTALL)
    if not blocks:
        return []

    mmd_dir = Path(work_dir) / "_mermaid"
    mmd_dir.mkdir(parents=True, exist_ok=True)

    # Write config and CSS for Chinese font support
    config = mmd_dir / "config.json"
    config.write_text(json.dumps({
        "theme": "default",
        "themeVariables": {
            "fontFamily": '"Noto Sans SC", "Microsoft YaHei UI", sans-serif',
            "fontSize": "14px"
        }
    }), encoding="utf-8")

    css = mmd_dir / "mermaid.css"
    css.write_text(
        '.node rect, .node polygon, .nodeLabel, .edgeLabel, '
        '.cluster-label, span { font-family: "Noto Sans SC", "Microsoft YaHei UI", sans-serif !important; }',
        encoding="utf-8"
    )

    png_paths = []
    for idx, block in enumerate(blocks):
        mmd_file = mmd_dir / f"diagram_{idx}.mmd"
        mmd_file.write_text(block.strip(), encoding="utf-8")
        png_file = mmd_dir / f"diagram_{idx}.png"

        cmd = [
            "npx", "--yes", "@mermaid-js/mermaid-cli",
            "-i", str(mmd_file),
            "-o", str(png_file),
            "-c", str(config),
            "-C", str(css),
            "-s", str(scale),
            "-w", str(width),
            "-b", "transparent",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", shell=True)
        if result.returncode != 0:
            print(f"[WARN] Mermaid render failed for diagram {idx}: {result.stderr.strip()}", file=sys.stderr)
        else:
            png_paths.append(str(png_file))
            print(f"[INFO] Mermaid diagram {idx+1}/{len(blocks)} rendered: {png_file.name}")

    return png_paths


# ─── PDF rendering ───────────────────────────────────────────────────

def render_pdf(html_content, output_path, title="Document"):
    """Render HTML to PDF via Playwright."""
    from playwright.sync_api import sync_playwright

    # Write temp HTML (use .html extension, NOT .pdf — Chromium treats .pdf as download)
    tmp_html = Path(output_path).parent / "_tmp_render.html"
    tmp_html.write_text(html_content, encoding="utf-8")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(tmp_html.as_uri())
        page.wait_for_load_state("networkidle")

        header = (
            f'<div style="font-size:8pt;color:#888;width:100%;text-align:center;'
            f'font-family:Microsoft YaHei UI,sans-serif;">{escape_html(title)}</div>'
        )
        footer = (
            '<div style="font-size:8pt;color:#888;width:100%;text-align:center;'
            'font-family:Microsoft YaHei UI,sans-serif;">'
            '<span class="pageNumber"></span> / <span class="totalPages"></span></div>'
        )

        page.pdf(
            path=str(output_path),
            format="A4",
            margin={"top": "20mm", "bottom": "25mm", "left": "18mm", "right": "18mm"},
            print_background=True,
            display_header_footer=True,
            header_template=header,
            footer_template=footer,
        )
        browser.close()

    tmp_html.unlink(missing_ok=True)


# ─── Cleanup ─────────────────────────────────────────────────────────

def cleanup(work_dir):
    """Remove intermediate files: _mermaid/ directory."""
    mmd_dir = Path(work_dir) / "_mermaid"
    if mmd_dir.exists():
        shutil.rmtree(mmd_dir, ignore_errors=True)
        print(f"[INFO] Cleaned up: {mmd_dir}")


# ─── Main ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Convert markdown to PDF via Playwright")
    parser.add_argument("input", help="Input markdown file")
    parser.add_argument("-o", "--output", help="Output PDF file (default: <input>.pdf)")
    parser.add_argument("--work-dir", help="Working directory for temp files (default: input dir)")
    parser.add_argument("--mermaid-scale", type=int, default=4, help="Mermaid render scale (default: 4)")
    parser.add_argument("--mermaid-width", type=int, default=2000, help="Mermaid render width (default: 2000)")
    parser.add_argument("--img-width", type=int, default=85, help="Image width %% in PDF (default: 85)")
    parser.add_argument("--title", default="", help="Page header title (default: input filename)")
    parser.add_argument("--keep-temp", action="store_true", help="Keep intermediate files")
    args = parser.parse_args()

    md_path = Path(args.input)
    if not md_path.exists():
        print(f"[ERROR] File not found: {md_path}", file=sys.stderr)
        sys.exit(1)

    # Defaults
    output_path = Path(args.output) if args.output else md_path.with_suffix(".pdf")
    work_dir = Path(args.work_dir) if args.work_dir else md_path.parent
    work_dir.mkdir(parents=True, exist_ok=True)
    title = args.title or md_path.stem

    print(f"[INFO] Reading: {md_path}")
    md_text = md_path.read_text(encoding="utf-8")

    # Render Mermaid diagrams
    print("[INFO] Rendering Mermaid diagrams ...")
    mermaid_pngs = render_mermaid(md_text, work_dir, args.mermaid_scale, args.mermaid_width)

    # Convert markdown to HTML
    print("[INFO] Converting markdown to HTML ...")
    body_html = md_to_html(md_text, mermaid_pngs)

    # Build full HTML
    css = build_css(args.img_width)
    full_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><style>{css}</style></head>
<body>{body_html}</body></html>"""

    # Render PDF
    print(f"[INFO] Rendering PDF to: {output_path}")
    render_pdf(full_html, output_path, title)

    # Cleanup
    if not args.keep_temp:
        cleanup(work_dir)

    size_kb = output_path.stat().st_size / 1024
    print(f"[OK] PDF generated: {output_path} ({size_kb:.0f} KB)")


if __name__ == "__main__":
    main()
