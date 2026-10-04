# 翻译计划 plan.json

坐标、尺寸单位都是 pt（16:9 课件一般 960×540）。`shape` 用 inventory 里的数字 id（cNvPr id，同一页内唯一）。`p` 是段落序号（inventory 里的 `p0`、`p3`……，空段落也占序号）。**所有 op 里的 `p`（包括 covers、skip）一律指原稿的序号**，前面插了中文也不用换算；同一形状可以分多个 op 写。

组合（group）里的形状不能移动或改尺寸（`adjust` 只能用 `font_scale`）；要挪就加独立 textbox。

```json
{
  "defaults": {"min_pt": 12, "scale": 0.75, "title_scale": 0.5, "cell_scale": 0.85,
               "color": null, "ea_font": null},
  "slides": [
    {"slide": 73, "ops": [ ... ]}
  ]
}
```

`defaults`：`scale` 正文中文相对英文的字号比例；`color` 如 `"1F4E79"` 给所有中文统一上色（默认 null = 跟随主题，和课件已有中文一致）；`ea_font` 指定中文字体（默认跟随主题，Mac 上渲染为等线）。

## 操作

| op | 用途 | 字段 |
|---|---|---|
| `para_after` | 在英文段落**下面**插入中文段落（同一文本框，与英文文字左对齐、无项目符号、继承层级缩进） | `shape`, `items:[{p, zh, scale?}]`, `space_before_pt?` |
| `para_after` + `inline:true` | 中文接在英文**同一行**后面（单行说明、短标签） | item 里加 `"inline": true`, `sep?`（默认两个空格） |
| `cells` | 表格单元格里在英文下面加中文；中文继承该格英文的粗体和颜色 | `shape`, `items:[{r, c, zh}]`, `scale?`, `table_scale?`（整表英文字号和行高比例）, `table_box?:{x?, y?, w?}`（移动/加宽表格，列宽按比例） |
| `textbox` | 新建独立中文文本框（标题译文、图片标注、公式释义） | `x, y, w, h`, `zh` 或 `lines:[...]`, `pt`(默认16), `align`(l/ctr/r), `anchor`(t/ctr/b), `fill?`, `name?`, `covers?` |
| `adjust` | 移动/缩放原有元素 | `shape`, 绝对 `x/y/w/h` 或相对 `dx/dy/dw/dh`；`font_scale`（整框英文字号比例） |
| `existing` | 声明已有中文文本框覆盖了哪些英文 | `shape`（中文框 id）, `covers:[{shape, p?}]`（省略 p = 整个形状） |
| `skip` | 声明不翻译 | `shape`, `p?:[段落序号 或 "r5c2" 单元格]`, `why` |

任何 op 都可以带 `covers:[{shape, p?}]` 告诉覆盖检查"这条英文已由此处中文覆盖"（例如标题 textbox 覆盖标题形状）。

## 执行顺序

同一页内按列表顺序执行。先 `adjust`（缩英文）再 `para_after`，中文字号按缩后的英文计算。

## 示例（第 73 页：要点 + 两个 OLE 公式）

```json
{"slide": 73, "ops": [
  {"op": "textbox", "name": "标题", "x": 590, "y": 70, "w": 240, "h": 40, "pt": 24,
   "zh": "CPU 性能方程", "covers": [{"shape": 142338}]},
  {"op": "adjust", "shape": 142339, "font_scale": 0.8},
  {"op": "para_after", "shape": 142339, "items": [
    {"p": 0, "zh": "程序的 CPU 执行时间可以用两种方式表示："},
    {"p": 1, "zh": "以时长表示 =>"}]},
  {"op": "adjust", "shape": 142341, "dy": 9},
  {"op": "textbox", "name": "公式1", "x": 366, "y": 227, "w": 552, "h": 22, "pt": 13,
   "zh": "CPU 时间 = 程序的 CPU 时钟周期数 × 时钟周期时长"}
]}
```

新建的形状都以 `ZH ` 开头命名；脚本据此判断某页是否已处理过。
