# Claude Code Skills

> A collection of custom skills for [Claude Code](https://claude.ai/code), enhancing AI-assisted development workflows.

**[中文文档](./README.zh-CN.md)**

## Skills

### [md2pdf](./skills/md2pdf/) — Markdown to PDF

Convert Markdown files to high-quality PDF via Playwright (Chromium). Native CJK/Chinese text support, Mermaid diagram rendering, compact layout with no tofu (black box) issues.

```bash
python scripts/md2pdf.py input.md -o output.pdf
```

**Key features:**
- CJK/Chinese text rendered correctly in all contexts (headings, code blocks, tables)
- Mermaid diagrams auto-rendered as high-resolution PNG images
- Compact layout optimized for technical documents
- Automatic cleanup of intermediate files

---

## Installation

### Install a single skill

Copy the skill folder to your Claude Code skills directory:

```bash
# macOS/Linux
cp -r skills/<skill-name> ~/.claude/skills/

# Windows
xcopy /E /I skills\<skill-name> %USERPROFILE%\.claude\skills\<skill-name>
```

### Install all skills

```bash
# macOS/Linux
cp -r skills/* ~/.claude/skills/

# Windows
xcopy /E /I skills\* %USERPROFILE%\.claude\skills\
```

## Dependencies

Each skill may have its own dependencies. See individual skill folders for details.

**md2pdf dependencies:**

- Python 3.10+
- `playwright` — `pip install playwright && playwright install chromium`
- `mermaid-cli` — `npm install -g @mermaid-js/mermaid-cli` (optional, only needed for Mermaid diagrams)
- System fonts: Microsoft YaHei / Noto Sans SC / SimHei (for Chinese rendering)

## Repository Structure

```
claude-skills/
├── README.md                      # English documentation
├── README.zh-CN.md                # 中文文档
├── .gitignore
└── skills/
    └── md2pdf/                    # Markdown to PDF
        ├── SKILL.md               # Skill definition
        └── scripts/
            └── md2pdf.py          # Conversion script
```

## Adding New Skills

1. Create a new folder under `skills/`
2. Add a `SKILL.md` with skill definition
3. Update both `README.md` and `README.zh-CN.md` with bilingual descriptions

## License

MIT License
