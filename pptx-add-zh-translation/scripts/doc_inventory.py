"""List what needs translating in a Word (.docx) or Markdown (.md) file.

Usage: python3 doc_inventory.py in.docx|in.md out_dir
Writes out_dir/inventory.md (one line per block, full English text) and
out_dir/inventory.json. Prints line ranges of inventory.md per 40 blocks.
"""
import argparse
import json
from pathlib import Path


def load(path):
    if path.lower().endswith(".docx"):
        from docx_model import Docx
        return Docx(path)
    if path.lower().endswith((".md", ".markdown")):
        from md_model import Markdown
        return Markdown(path)
    raise SystemExit("only .docx / .md are supported here (PPTX: inventory.py, PDF: pdf_inventory.py)")


def describe(b, is_md):
    bits = [b["role"]]
    if b.get("level") is not None and b["role"] in ("heading", "list"):
        bits.append(("h%d" if b["role"] == "heading" else "lvl%d") % b["level"])
    if is_md:
        s, e = b["start"] + 1, b["end"] + 1
        bits.append("L%d" % s if s == e else "L%d-%d" % (s, e))
        if b.get("qp"):
            bits.append("quote")
    else:
        if b.get("style"):
            bits.append("[%s]" % b["style"])
        if b.get("loc"):
            bits.append(b["loc"])
        if b.get("math"):
            bits.append("math")
    return " ".join(bits)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("out_dir")
    a = ap.parse_args()
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    doc = load(a.source)
    is_md = not a.source.lower().endswith(".docx")
    blocks = doc.blocks()
    counts = {}
    for b in blocks:
        counts[b["kind"]] = counts.get(b["kind"], 0) + 1
    md = ["# inventory: %s" % Path(a.source).name,
          "blocks: %d  (%s)" % (len(blocks), ", ".join("%s %d" % kv for kv in sorted(counts.items()))),
          "kind: en = 需要中文；zh = 已有中文（用 existing 声明）；misc = 数字/符号；code/math/html/meta/image = 不需要翻译",
          ""]
    ranges, first = [], len(md) + 1
    for i, b in enumerate(blocks):
        text = b["text"].replace("\n", " ⏎ ")
        if b["kind"] in ("code", "meta", "html") and len(text) > 80:
            text = text[:80] + " …"
        if b.get("math") and not b["text"].strip():
            text = "(公式) " + b["math"][:80]
        md.append("%s | %s | %s | %s" % (b["id"], b["kind"], describe(b, is_md), text))
        if (i + 1) % 40 == 0 or i == len(blocks) - 1:
            ranges.append((blocks[i - (i % 40)]["id"], b["id"], first, len(md)))
            first = len(md) + 1
    (out / "inventory.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    js = [{k: v for k, v in b.items() if k not in ("el", "mirror")} for b in blocks]
    json.dump(js, open(out / "inventory.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("wrote %s/inventory.md (%d blocks: %s)" % (out, len(blocks),
          ", ".join("%s %d" % kv for kv in sorted(counts.items()))))
    for s, e, a_, b_ in ranges:
        print("  %s–%s: lines %d-%d" % (s, e, a_, b_))


if __name__ == "__main__":
    main()
