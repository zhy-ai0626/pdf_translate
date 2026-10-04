---
name: pptx-add-zh-translation
description: 在英文课件的原页面上补充中文翻译（同页双语，保留英文，不是把英文替换成中文）。支持 PPTX，也支持只有 PDF 的课件（输出双语 PDF，英文保持矢量）。标题、正文要点、表格单元格、图片里的英文标注、公式都逐条补中文；必要时小幅移动/缩小原元素；输出双语文件并渲染检查遮挡和溢出（可在 Claude Code、Codex、DeepSeek Harness 中运行）。用户说"给 PPT/PDF 课件加中文翻译""双语课件""在英文幻灯片上加中文""中英对照""翻译课件但保留英文"时使用，即使没说 skill 名字。不用于：整份替换成中文、Word 文档或普通 PDF 文章/论文翻译、新建幻灯片。
---

# 在英文幻灯片上补充中文翻译

目标：学生打开原英文课件，每一条英文旁边/下面都能看到对应的中文，版面不乱。

**输入是 PDF 时**：先问有没有原始 PPTX（效果更好）；没有就读 `references/pdf-mode.md` 走 PDF 模式。下面的规则、术语、流程同样适用，计划格式和工具换成 PDF 版。

## 不可违反的规则

1. **原文件永不覆盖**。输出 `<原名>_双语.pptx`（样稿 `_双语样稿.pptx`）到原文件旁边。计划永远应用在原始文件上（脚本对已处理页默认跳过）。
2. **同页双语**：中文与英文在同一页。可以小幅移动或缩小原有元素（英文字号最低缩到原来的 0.75），不加新页。
3. **逐条对应**：标题、每条要点、表格每个单元格、图片中的重要英文标注、公式都要有中文。不翻译的内容（URL、Credit、页码、作为术语保留的缩写如 SRAM/DRAM）必须在计划里用 `skip` 写明理由。
4. **已有中文保留不动**：用户手工加过的中文文本框不改文字，用 `existing` 声明它覆盖了哪些英文；只有它和别的元素相撞时才移动它。不能因为某页有中文就认为整页已翻译——缺的条目照样补。
5. **中文字号下限 12pt**（渲染后的实际字号）。放不下先挪位置、再缩英文、再缩中文，仍放不下就报告给用户，不要硬塞。
6. 翻译忠实原意；额外解释不写进译文。术语按 `references/glossary-computer-architecture.md`（其他学科新建同格式术语表），缩写保留英文并在首次出现时给中文：`算术逻辑单元（ALU）`。数字、单位、公式符号原样保留。

## 运行环境（先确定 PY 和渲染器）

脚本在本 skill 目录的 `scripts/` 下（下文 `<skill>` = 本 SKILL.md 所在目录，各 harness 路径不同，用绝对路径调用）。只依赖 lxml；PyMuPDF 可选。

| Harness | Python（下文 PY） | 渲染器（`render_check.py --renderer`） |
|---|---|---|
| Claude Code | `python3`（需 lxml；有 pymupdf 时检查最准） | `auto`：macOS 有 PowerPoint 就用它 |
| Codex | `python3`；调用 PowerPoint 的 `osascript` 需要申请沙箱外执行/GUI 自动化授权 | `auto`；授权被拒时用 `soffice` 或 `none` |
| DeepSeek Harness | 调 `load_workspace_dependencies`，用它返回的 Python（自带 lxml，无 PyMuPDF）。**不要 pip 安装** | `lok`：内置 LibreOffice Kit。把已加载 office 技能里 *Installed LibreOffice Kit* 的 node / cli 路径传给 `--lok-node --lok-cli`（macOS 上不传会自动找 DSH 安装目录）。用户明确要求才改用 PowerPoint |

没有 PyMuPDF 时：`render_check.py` 仍导出 PDF，PNG 由 LibreOffice Kit 生成，版面检查改为**按 XML 估算**（输出 `check mode: estimated-from-xml`，误差约 10–20pt：估算的 error 要对照 PNG 确认，不能直接当成真问题）；`layout_hints.py` 直接传原稿 `.pptx`。LibreOffice 缺 Consolas 等字体，版面只是近似。

## 工具

| 脚本 | 作用 |
|---|---|
| `PY <skill>/scripts/inventory.py deck.pptx out/ [--pages 4,9-12]` | 读出每页的形状、段落（层级/字号）、表格单元格、坐标(pt)、已有中文、按段落动画的形状、OLE 公式/图片/视频。输出 `inventory.md`（给你读）和 `inventory.json` |
| `PY <skill>/scripts/apply_plan.py src.pptx plan.json out.pptx --report rep.json` | 按计划插入中文，只重写被改动的 slide XML（媒体、公式、动画原样保留）。会列出**未覆盖的英文**（`uncovered:`） |
| `PY <skill>/scripts/layout_hints.py <原稿.render.pdf 或 原稿.pptx> hints.md` | 每行文字的位置（pt）、图片框、标题右侧空位。**不看 PNG 也能算坐标** |
| `PY <skill>/scripts/render_check.py deck.pptx out/ --pages ... [--renderer ...]` | 隐藏页取消隐藏后导出 PDF、生成 PNG，检查中文字号过小、出界、文字重叠/过近、中文压图 |

python-pptx 打不开含 `mc:AlternateContent`/OLE 的课件（`has_ph_elm` 报错），所以脚本全部直接操作 XML；不要换回 python-pptx。

计划 JSON 的全部操作见 `references/plan-schema.md`；各类页面怎么排版见 `references/layout-rules.md`。**写计划前先读这两份。**

## 流程

1. **确认范围**：哪个文件、哪些页（默认全部）、是否先做样稿。原稿有大量已有中文、动画、视频时先告诉用户。
2. **盘点**：`inventory.py` 全册跑一次；`render_check.py` 渲染原稿，再用 `layout_hints.py` 从它的 PDF 生成位置提示。图片里的英文、公式内容从 PNG 或已有的逐页视觉笔记中获取。记下原稿本来就有的问题（检查结果里的 `warn(pre-existing?)`），不要把它们算成自己造成的。
3. **术语表**：读已有中文页，沿用里面的译法；把本课件新出现的术语补进术语表（fault/error/failure 等易混词要区分）。
4. **分批写计划**：每批约 8–10 页，一页一个 entry。逐页对照 `inventory.md` 和该页 PNG：
   - 每个英文段落/单元格 → `para_after` / `inline` / `cells` / `textbox`；
   - 图片里的英文 → 在附近加 `textbox` 标注（从 PNG 估坐标：PNG 像素 × 72 / dpi = pt）；
   - 已有中文 → `existing`；不译 → `skip`。
   - 用户不要求看图时：图片标注不放进图里，改为在图片旁空白处加一个"图中：English 中文；…"说明框。
   - 页数多时可以按批分给子代理并行写计划（每份计划只含自己的页），最后合并成一份再应用；渲染只能串行（PowerPoint 只有一个实例）。没有子代理的 harness 就按批顺序做。
5. **应用 + 渲染 + 看图**：`apply_plan.py` 后 `uncovered:` 必须为空（或已 skip）；`render_check.py` 的 error 必须为 0；然后**逐页打开 PNG 亲眼看**（检查器只管几何，不管"中文是不是对着正确的英文""公式是否和要点对齐"）。有问题改计划，重新从原稿应用。
6. **交付**：输出双语文件 + 简短报告：处理页数、每页 error/warning 结论、跳过了什么及原因、需要用户人工决定的页（放不下、动画页、视频页）。

## 常见坑（都在样稿里踩过）

- 段落插入后下方内容整体下移，**旁边独立放置的公式/图片不会跟着动**——渲染后对照 PNG，用 `adjust` 的 `dy` 把公式挪回对应要点的高度。脚本会同步 OLE 的 Fallback 副本和 VML 图层，不会出现重影。
- 标题框通常是底部对齐，往标题里加段落会把英文往上顶；标题中文用独立 `textbox` 放在英文标题右侧同一行（右侧空间不够就放标题下方并把标题上移）。
- 表格加中文后行变高会超出页面：先 `table_box` 加宽表格（减少换行），再 `table_scale` 缩英文，最后才缩中文。
- 按段落播放动画的形状（inventory 标 `PARA-ANIMATED`）不能插段落，否则动画错位——改用 `textbox`，并告诉用户这些中文不会随动画出现。
- 隐藏页 PowerPoint 默认不导出，`render_check.py` 已自动取消隐藏（仅渲染副本），所以 PDF 第 N 页 = 第 N 张幻灯片。
- 视频页只翻译可见文字，不要编造视频内容。
