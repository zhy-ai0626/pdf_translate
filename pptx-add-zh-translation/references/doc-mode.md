# Word / Markdown 模式（.docx / .md）

英文 Word 文档（讲义、实验指导、作业说明、论文稿）或 Markdown 笔记（README、Obsidian 笔记）逐段补中文，**英文保留**，中文紧跟在对应英文后面。规则同 SKILL.md：原文件不覆盖（输出 `<原名>_双语.docx` / `<原名>_双语.md`）、逐条对应、已有中文不动、不译的写 `skip` 和理由、术语按术语表。

和幻灯片的区别：文档会自动重排，没有"放不下"的问题，所以**没有坐标、没有缩字**；工作量主要在翻译本身和校读。

## 工具

| 脚本 | 作用 |
|---|---|
| `PY <skill>/scripts/doc_inventory.py in.docx\|in.md out/` | 每个块一行：`id \| kind \| 角色/位置 \| 完整英文`。结尾打印每 40 块在 `inventory.md` 里的行号范围，按批读 |
| `PY <skill>/scripts/doc_apply.py in plan.json out --report rep.json --review pairs.md [--merge b2.json …]` | 应用计划，打印 `uncovered:`；`--review` 生成"英文 → 中文"对照清单供校读 |
| `PY <skill>/scripts/doc_render.py out.docx chk/ [--pages 1-3]` | 仅 Word：用 WPS（`wpscli word2pdf`）或 LibreOffice 导出 PDF 和 PNG，看版面 |

只依赖 lxml（Word）或纯 Python（Markdown）；`doc_render.py` 出 PNG 需要 PyMuPDF。不要用 python-docx 改文件（会丢 mc:AlternateContent 里的文本框等），脚本直接改 XML、未改动的部件原样复制。

## 块 id

- **Word**：每个段落一个块。`B` 正文、`F` 脚注、`N` 尾注、`H` 页眉页脚；数字是段落在该部件里的序号（空段落也占号，所以 id 稳定）。表格单元格里的段落也是普通块，位置列写 `table2 r1c3`；文本框里的写 `textbox`（mc:Fallback 里的副本自动同步，不单独列出）。
- **Markdown**：每个标题/段落/列表项/引用段/callout 标题一个块 `B<n>`；表格每个单元格一个块 `B<n>.r<行>c<列>`（表头 = r0，分隔行不算）。
- 角色：`heading` `para` `list` `cell` `caption` `callout` `footnote`；`header`（页眉页脚）和 `toc`（目录）不强制翻译。
- `kind`：`en` 必须有中文；`zh` 已有中文；`misc` 数字符号；`code` `math` `html` `meta`（front matter）`image` 不需要翻译、也不能改。Word 里等宽字体（Courier/Consolas…）或 Code 样式的段落判为 `code`；普通字体排的代码、命令和程序输出（实验指导里常见）按文本特征识别（`scripts/codetext.py`，Word 连续段落里三成以上是代码时整段都算），Markdown 里没放进代码块的代码也一样。没认出的代码行写 `skip`（why: 代码），不要翻译。

## 计划 plan.json

```json
{
  "defaults": {"heading": null, "md_list": "soft", "sep": "  ", "tight": true,
               "scale": 1.0, "color": null, "ea_font": null},
  "items": [
    {"b": "B1", "zh": "统计学习导论"},
    {"b": "B4", "zh": "监督学习使用有标签的数据。"},
    {"b": "B9", "zh": "线性回归是一种简单的方法。", "covers": ["B10"]},
    {"b": "B12", "zh": "偏差与方差", "place": "below"},
    {"b": "B8.r1c1", "zh": "残差平方和"},
    {"existing": "B14", "covers": ["B13"]},
    {"skip": ["H1", "B20"], "why": "页眉；作者姓名"}
  ]
}
```

| 项 | 含义 |
|---|---|
| `{"b", "zh"}` | 给块加中文。`zh` 里的 `\n` 换行 |
| `place` | `below`（默认）：英文下面新起一段；`inline`：接在英文同一行末尾（用 `sep` 隔开） |
| `covers` | 这段中文同时覆盖的其他块（英文一句话被拆成几段时，中文写在最后一段并 covers 前面的） |
| `existing` + `covers` | 已有中文段落覆盖了哪些英文 |
| `skip` + `why` | 不翻译（姓名、学号、代码、引用条目、URL……） |

defaults：
- `heading`：标题的默认放法。Word 默认 `inline`（"Introduction  引言"，导航窗格和目录里也是双语）；Markdown 默认 `below`——**Markdown 标题改 inline 会改变标题锚点，`[[文件#标题]]` 链接会断**，脚本会提示。
- `md_list`：Markdown 列表项的中文放法。`soft`（默认）：缩进到列表文字列的续行，列表保持紧凑，Obsidian 显示为换行，GitHub 等 CommonMark 渲染器显示为同一行接在后面；`paragraph`：空一行再写（各渲染器都是独立一行，但列表变"松散"、行距变大）；`br`：英文行尾加 `<br>`。
- `tight`（Word）：英文段落段后距改 0、中文段段前距 0，让一对中英文挨在一起，对与对之间保留原来的段距。
- `scale` / `color` / `ea_font`（Word）：中文字号比例（默认 1.0，和英文同号）、颜色（如 `"1F4E79"`）、中文字体（默认跟随文档主题）。

## 各类内容怎么放（脚本自动处理的部分）

- **Word 正文段落**：中文段复制英文段的段落格式（对齐、缩进、行距），去掉编号、分页、分节符（分节符移到中文段上，节不会被拆开）；字符格式取英文段里字数最多的那个 run（粗体、颜色跟随；超链接样式去掉）。
- **Word 列表**：中文段不带项目符号/编号，左缩进对齐到英文文字（从 numbering.xml 读层级缩进）；样式自带编号的（List Bullet）用 numId=0 关掉。
- **Word 标题**：默认 inline。`below` 时中文段去掉标题样式（不进目录、不被编号），加粗、跟在标题后不分页。
- **Word 表格**：中文段加在单元格里对应英文段下面；行会变高，表格可能跨页。
- **Word 文本框**：中文加在框里；框是固定高度时可能溢出被裁掉——渲染后看 PNG，溢出就缩短译文，仍放不下就把这块改成 `skip`（why 写“文本框放不下”）并列进报告，由用户决定。
- **Markdown 段落/引用/callout**：段落空一行写中文；引用块里自动加 `>` 前缀；callout 标题默认 inline（`> [!note] Key Idea  核心思想`）。
- **Markdown 表格**：单元格变成 `English<br>中文`，`|` 自动转义。
- **不碰的内容**：代码块、`$$` 公式块、HTML、front matter、图片行、行内代码和行内公式（翻译时原样照抄 `` `code` `` 和 `$x$`，链接保留目标、只译显示文字）。

## 流程

1. `doc_inventory.py` 跑一次，看 kind 统计；文档长（>80 块）就按 inventory 打印的行号范围分批，每批 40–80 块。
2. 读已有中文（`zh` 块）沿用译法；新术语补进术语表（同 SKILL.md 第 3 步）。
3. 写计划：每个 `en` 块一项；`zh` 块紧挨着英文的大概率是已有译文，用 `existing`；姓名、学号、日期、参考文献条目、代码、URL 写 `skip`。
4. `doc_apply.py … --report rep.json --review pairs.md`：`uncovered:` 必须为空（页眉页脚、目录列在 `optional` 里，可不译，但要在报告里说明）。
5. 校读 `pairs.md`：译文对着的是不是正确的英文、术语是否统一、有没有漏译半句。
6. Word：`doc_render.py` 看 PNG（第一次看全部页；长文档至少看有表格、文本框、列表、标题的页），记下页数变化（原稿也渲染一次对比）。Markdown：在 Obsidian 或预览里看，或直接读输出文件里改动的地方。
7. 交付报告：输出路径、翻译块数、skip 了什么及原因、可选未译（页眉/目录）、Word 页数变化、文本框溢出等需要人工决定的地方；看过哪些页的 PNG 如实写。

## 注意

- 计划永远应用在原文件上；改计划后重新从原文件生成，不要在 `_双语` 文件上再跑一次（会把中文当成已有中文）。
- Word 修订模式（track changes）下的删除文字不会出现在 inventory 里；插入的文字照常翻译。
- 目录（TOC 域）不用逐条翻：标题 inline 双语后，用户在 Word/WPS 里"更新目录"即可。
- 公式（OMML）不译；需要释义时在公式下一段的中文里写，不要改公式本身。
