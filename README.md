# pdf_translate

一个 Agent Skill：**在英文课件的原页面上补充中文翻译**（同页双语，保留英文，不是替换）。

- **PPTX**：直接改幻灯片 XML，在每条英文旁/下插入中文，输出 `<原名>_双语.pptx`。
- **PDF**（只有 PDF 课件时）：英文保持矢量、可选中；在段落下方把页面（或单栏）切开下移腾出空间，背景、色块、表格边框连续；放不下时整栏等比缩小（不低于 75%），输出 `<原名>_双语.pdf`。
- 标题、正文要点、表格单元格、图片里的英文标注、公式逐条补中文；自带渲染检查（中文过小、出界、重叠、压图、压线）。

可在 **Claude Code**、**Codex**、**DeepSeek Harness** 中使用。

## 安装

把 `pptx-add-zh-translation/` 目录放进你的 skills 目录，例如：

```bash
git clone https://github.com/zhy-ai0626/pdf_translate.git
cp -r pdf_translate/pptx-add-zh-translation ~/.claude/skills/      # Claude Code
# Codex / DeepSeek Harness：放到 ~/.agents/skills/
```

依赖：

- Python 3 + `lxml`（PPTX 模式）
- `pymupdf`（PDF 模式；PPTX 模式下可选，用于更准确的渲染检查）
- 渲染 PPTX：macOS 上的 Microsoft PowerPoint，或 LibreOffice / DeepSeek Harness 内置的 LibreOffice Kit

DeepSeek Harness 自带的 Python 没有 PyMuPDF：PDF 脚本会自动改用系统里装有 PyMuPDF 的 `python3`，也可以设置 `PPTX_ZH_PDF_PY=/path/to/python3`。

## 使用

在对话里说"给这份 PPT/PDF 课件加中文翻译""做成中英对照"之类即可触发。流程和规则见 [`SKILL.md`](pptx-add-zh-translation/SKILL.md)，PDF 模式见 [`references/pdf-mode.md`](pptx-add-zh-translation/references/pdf-mode.md)。

## 目录

```
pptx-add-zh-translation/
├── SKILL.md                     规则与流程
├── references/                  计划格式、排版做法、PDF 模式、术语表
├── scripts/                     inventory / apply / 渲染检查（PPTX 与 PDF）
└── assets/                      示例计划
```
