# PDF 模式（只有 PDF 课件时）

有原始 PPTX 就用 PPTX 流程（可以改文本框、效果最好）。只有 PDF 时（PowerPoint 导出的、LaTeX Beamer、扫描件）用本模式。规则和 SKILL.md 相同：同页双语、逐条对应、中文 ≥12pt、英文缩放不低于 0.75、原文件不覆盖，输出 `<原名>_双语.pdf`（样稿 `_双语样稿.pdf`）。

## 原理（写计划前要知道）

- 英文保持矢量、可选中，不会被转成图片。改动过的页由原页的裁切片段重新拼成。
- PDF 不能重排文字。给中文腾地方只能**把下面的内容整体下移**：在段落下方找一条"干净"的横线（不穿过文字、图片、曲线或斜线）切开，下面的部分往下移。切开处的空隙用切线位置一条细片拉伸填满，所以背景、色块、表格竖线和底色都会连续。
- 左右分栏时只切这一栏（column cut），另一栏不动；每栏各自计算。
- 一栏放不下时，这一栏从第一个加中文的段落开始整体等比缩小（`en_scale`），低于 0.75 报 `too_full`。底部页脚区（页码、校徽、课程代码）不动。
- 改动过的页上的超链接会丢失；没有 op 的页原样复制。

## 依赖

需要 PyMuPDF。当前 Python 没有时（DeepSeek Harness 自带 Python），脚本会自动改用装有 PyMuPDF 的 `python3` 重新运行；找不到就报错退出。这时可以设置 `PPTX_ZH_PDF_PY=/path/to/python3`，或者改在 Claude Code / Codex 里运行这一步。**不要在 DSH 里 pip 安装。**

## 工具

| 脚本 | 作用 |
|---|---|
| `PY <skill>/scripts/pdf_inventory.py in.pdf out/ [--pages 3,5-9]` | 每页段落 `P1..Pn`（坐标 pt、字号、种类）、下方空白 `free`、能否切开（`cut ok` / `column cut` / `no cut`）、右侧空白、图片框、页脚区；同时导出原页 PNG（`pageNN.png`） |
| `PY <skill>/scripts/pdf_apply.py in.pdf plan.json out.pdf --report rep.json` | 应用计划，每页打印中文框数、英文缩放、error 和 `uncovered:` |
| `PY <skill>/scripts/render_check.py out.pdf chk/ [--pages ...]` | 直接检查 PDF：中文过小、出界、与英文重叠、压图；导出 PNG |

种类 `kind`：`en` 要翻译；`zh` 是已有中文；`footer` 是页脚区英文（可不译）；`misc` 是数字/符号。没有文字层（扫描件、整页是图）的页标 `SCANNED/IMAGE-ONLY`：从 PNG 读英文，全部用 `textbox`（坐标 pt = 像素 × 72 / dpi，默认 dpi 110）。

## 计划 plan.json

坐标都按**原页**的 pt 写（脚本会自动换算到下移/缩放后的位置）。`p` 用 inventory 的段落 id。

```json
{
  "defaults": {"min_pt": 12, "scale": 0.75, "title_scale": 0.5, "color": null, "font": null},
  "pages": [
    {"page": 6, "ops": [
      {"op": "right", "p": "P1", "zh": "数据的类型"},
      {"op": "below", "p": "P2", "zh": "结构化数据是定量的、高度组织化的……"},
      {"op": "textbox", "x": 525, "y": 478, "w": 330, "pt": 12, "zh": "图中：Structured Data 结构化数据", "covers": ["P5"]},
      {"op": "skip", "p": ["P7"], "why": "页码"}
    ]}
  ]
}
```

| op | 用途 | 字段 |
|---|---|---|
| `below` | 中文放在段落正下方，与英文文字左对齐；空间不够时自动切开下移（`room:"none"` 则不切，只在现有空白里缩字） | `p`, `zh`, `pt?`, `scale?`, `w?`, `dx?`, `dy?`, `align?`(l/ctr/r，配合 `w`/`dx` 让图框里的短标签居中), `fill?`, `room?` |
| `right` | 中文放在段落第一行右侧同一行（标题、短标签、短要点） | `p`, `zh`, `pt?`, `gap?`(默认10), `w?`, `dy?` |
| `textbox` | 任意位置的中文框（图中标注、整栏译文、扫描页） | `x, y, w`, `h?`, `zh` 或 `lines`, `pt`(默认16), `align`(l/ctr/r), `anchor`(t/ctr/b，需 h), `fill?`, `covers?` |
| `gap` | 在段落下方额外留白 | `after`, `h` |
| `move` | 移动/缩放一块原内容（段落或矩形） | `p` 或 `rect:[x0,y0,x1,y1]`, `dx`, `dy`, `scale?` |
| `existing` | 已有中文段落覆盖了哪些英文 | `p`（中文段落）, `covers:[...]` |
| `skip` | 不翻译 | `p:[...]`, `why` |

- 中文字号默认 = 英文字号 × `scale`（0.75），`right` 用在 ≥28pt 的标题上时 × `title_scale`（0.5）；都不低于 `min_pt`。
- 颜色默认跟随该段英文（红色标题配红色中文）；`textbox` 默认黑色。`color` 填 `"1F4E79"` 这类十六进制。
- `fill: "FFFFFF"` 给中文垫白底，压在图片或彩色背景上时用。
- `font` 可填字体文件路径；默认用 PyMuPDF 内置的 Droid Sans Fallback（无衬线，含中英文）。

## 排版做法

- **标题**：`right`。右侧放不下（报 `no_room_right`）改 `below`。
- **短要点、目录**：右侧空白够就用 `right`（不改动版面）；不够用 `below`。
- **长段落**：`below`。
- **一页很满**（`below` 会让英文缩到 0.8 以下）：优先 `right`；或者把整栏译文放进旁边空白的 `textbox`，用 `covers` 列出它覆盖的段落。
- **表格**：矢量表格（边框是线条）直接对每个单元格 `below`；同一行的单元格共用一次切开，整行变高，底色和竖线连续。表格本身是图片时（`no cut`），用 `textbox` + `fill` 放在表下方或旁边。
- **图片里的英文**：只标重要标注；在旁边空白处加 `textbox`（"图中：English 中文；…"），不要切图片。
- **公式**（Beamer 公式常是图片或零散符号）：不译符号；需要时在下面加一行 `textbox` 释义。零散的 `misc` 符号段落不用管。
- **`no cut`**：段落下面贴着图片、曲线形状（如云朵）或跨栏的内容。用 `right`、`textbox`，或先用 `move` 挪开挡住的东西。

## 检查

`pdf_apply.py` 的 error 要为 0、`uncovered:` 为空（页脚、`misc` 不算）；`render_check.py` 的 error 为 0。然后看 PNG：检查器只看几何，不判断"中文是否对着正确的英文"、白底有没有挡住内容、切开处是否拉伸出奇怪的条纹。有问题改计划，重新从原 PDF 应用。
