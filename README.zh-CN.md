# Claude Code 技能集

> [Claude Code](https://claude.ai/code) 自定义技能集合，增强 AI 辅助开发工作流。

**[English](./README.md)**

## 技能列表

### [md2pdf](./skills/md2pdf/) — Markdown 转 PDF

基于 Playwright (Chromium) 将 Markdown 文件转换为高质量 PDF。原生支持中文/CJK 文本，Mermaid 图表自动渲染，紧凑排版，无黑块（tofu）问题。

```bash
python scripts/md2pdf.py input.md -o output.pdf
```

**核心特性：**
- 中文/CJK 文本在所有场景下正确渲染（标题、代码块、表格）
- Mermaid 图表自动渲染为高清 PNG 图片嵌入 PDF
- 紧凑排版，适合技术文档
- 自动清理中间临时文件

---

## 安装

### 安装单个技能

将技能文件夹复制到 Claude Code 技能目录：

```bash
# macOS/Linux
cp -r skills/<skill-name> ~/.claude/skills/

# Windows
xcopy /E /I skills\<skill-name> %USERPROFILE%\.claude\skills\<skill-name>
```

### 安装全部技能

```bash
# macOS/Linux
cp -r skills/* ~/.claude/skills/

# Windows
xcopy /E /I skills\* %USERPROFILE%\.claude\skills\
```

## 依赖

每个技能可能有各自的依赖，请查看对应技能文件夹的说明。

**md2pdf 依赖：**

- Python 3.10+
- `playwright` — `pip install playwright && playwright install chromium`
- `mermaid-cli` — `npm install -g @mermaid-js/mermaid-cli`（可选，仅当包含 Mermaid 图表时需要）
- 系统字体：Microsoft YaHei / Noto Sans SC / SimHei（中文渲染）

## 仓库结构

```
claude-skills/
├── README.md                      # 英文文档
├── README.zh-CN.md                # 中文文档
├── .gitignore
└── skills/
    └── md2pdf/                    # Markdown 转 PDF
        ├── SKILL.md               # 技能定义
        └── scripts/
            └── md2pdf.py          # 转换脚本
```

## 添加新技能

1. 在 `skills/` 下创建新文件夹
2. 添加 `SKILL.md` 技能定义文件
3. 同步更新 `README.md` 和 `README.zh-CN.md` 的双语说明

## 许可证

MIT License
